"""
Provides Ruby specific instantiation of the LanguageServer class using Solargraph.
Contains various configurations and settings specific to Ruby.
"""

import json
import logging
import os
import pathlib
import shutil
import subprocess
import threading

from overrides import override

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings


class Solargraph(SolidLanguageServer):
    """
    Provides Ruby specific instantiation of the LanguageServer class using Solargraph.
    Contains various configurations and settings specific to Ruby.
    """

    def __init__(
        self, config: LanguageServerConfig, logger: LanguageServerLogger, repository_root_path: str, solidlsp_settings: SolidLSPSettings
    ):
        """
        Creates a Solargraph instance. This class is not meant to be instantiated directly.
        Use LanguageServer.create() instead.
        """
        solargraph_executable_path = self._setup_runtime_dependencies(logger, config, repository_root_path)
        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd=f"{solargraph_executable_path} stdio", cwd=repository_root_path),
            "ruby",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()
        self.service_ready_event = threading.Event()
        self.initialize_searcher_command_available = threading.Event()
        self.resolve_main_method_available = threading.Event()

        # Set timeout for Solargraph requests - Bundler environments may need more time
        self.set_request_timeout(120.0)  # 120 seconds for initialization and requests

    @override
    def is_ignored_dirname(self, dirname: str) -> bool:
        return super().is_ignored_dirname(dirname) or dirname in ["vendor"]

    @staticmethod
    def _setup_runtime_dependencies(logger: LanguageServerLogger, config: LanguageServerConfig, repository_root_path: str) -> str:
        """
        Setup runtime dependencies for Solargraph and return the command to start the server.
        """
        # Check if Ruby is installed
        try:
            result = subprocess.run(["ruby", "--version"], check=True, capture_output=True, cwd=repository_root_path)
            ruby_version = result.stdout.strip()
            logger.log(f"Ruby version: {ruby_version}", logging.INFO)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error checking for Ruby installation: {e.stderr}") from e
        except FileNotFoundError as e:
            raise RuntimeError("Ruby is not installed. Please install Ruby before continuing.") from e

        # Check for Bundler project (Gemfile exists)
        gemfile_path = os.path.join(repository_root_path, "Gemfile")
        gemfile_lock_path = os.path.join(repository_root_path, "Gemfile.lock")
        is_bundler_project = os.path.exists(gemfile_path)

        if is_bundler_project:
            logger.log("Detected Bundler project (Gemfile found)", logging.INFO)

            # Check if bundle command is available
            bundle_path = shutil.which("bundle")
            if not bundle_path:
                # Try common bundle executables
                for bundle_cmd in ["bin/bundle", "bundle"]:
                    bundle_full_path = (
                        os.path.join(repository_root_path, bundle_cmd) if bundle_cmd.startswith("bin/") else shutil.which(bundle_cmd)
                    )
                    if bundle_full_path and os.path.exists(bundle_full_path):
                        bundle_path = bundle_full_path if bundle_cmd.startswith("bin/") else bundle_cmd
                        break

            if not bundle_path:
                raise RuntimeError("Bundler project detected but 'bundle' command not found. Please install Bundler.")

            # Check if solargraph is in Gemfile.lock
            solargraph_in_bundle = False
            if os.path.exists(gemfile_lock_path):
                try:
                    with open(gemfile_lock_path) as f:
                        content = f.read()
                        solargraph_in_bundle = "solargraph" in content.lower()
                except Exception as e:
                    logger.log(f"Warning: Could not read Gemfile.lock: {e}", logging.WARNING)

            if solargraph_in_bundle:
                logger.log("Found solargraph in Gemfile.lock", logging.INFO)
                return f"{bundle_path} exec solargraph"
            else:
                logger.log(
                    "solargraph not found in Gemfile.lock. Please add 'gem \"solargraph\"' to your Gemfile and run 'bundle install'",
                    logging.WARNING,
                )
                # Fall through to global installation check

        # Check if solargraph is installed globally
        # First, try to find solargraph in PATH (includes asdf shims)
        solargraph_path = shutil.which("solargraph")
        if solargraph_path:
            logger.log(f"Found solargraph at: {solargraph_path}", logging.INFO)
            return solargraph_path

        # Fallback to gem exec (for non-Bundler projects or when global solargraph not found)
        if not is_bundler_project:
            gem_home = os.path.join(repository_root_path, ".venv", "gem_home")
            os.makedirs(gem_home, exist_ok=True)
            gem_env = os.environ.copy()
            gem_env["GEM_HOME"] = gem_home
            solargraph_exe = os.path.join(gem_home, "bin", "solargraph")

            runtime_dependencies = [
                {
                    "url": "https://rubygems.org/downloads/solargraph-0.51.1.gem",
                    "installCommand": f"gem install solargraph -v 0.51.1 --no-document --bindir {os.path.join(gem_home, 'bin')}",
                    "binaryName": "solargraph",
                    "archiveType": "gem",
                }
            ]

            dependency = runtime_dependencies[0]
            try:
                result = subprocess.run(
                    ["gem", "list", "^solargraph$", "-i"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=repository_root_path,
                    env=gem_env,
                )
                if result.stdout.strip() == "false":
                    logger.log("Installing Solargraph...", logging.INFO)
                    subprocess.run(
                        dependency["installCommand"].split(),
                        check=True,
                        capture_output=True,
                        cwd=repository_root_path,
                        env=gem_env,
                    )

                return solargraph_exe
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to check or install Solargraph. {e.stderr}") from e
        else:
            raise RuntimeError(
                "This appears to be a Bundler project, but solargraph is not available. "
                "Please add 'gem \"solargraph\"' to your Gemfile and run 'bundle install'."
            )

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for the Solargraph Language Server.
        """
        root_uri = pathlib.Path(repository_absolute_path).as_uri()
        initialize_params = {
            "capabilities": {
                "workspace": {
                    "workspaceEdit": {"documentChanges": True},
                    "didChangeConfiguration": {"dynamicRegistration": True},
                    "didChangeWatchedFiles": {"dynamicRegistration": True},
                    "symbol": {
                        "dynamicRegistration": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                    },
                    "executeCommand": {"dynamicRegistration": True},
                },
                "textDocument": {
                    "synchronization": {"dynamicRegistration": True, "willSave": True, "willSaveWaitUntil": True, "didSave": True},
                    "hover": {"dynamicRegistration": True, "contentFormat": ["markdown", "plaintext"]},
                    "signatureHelp": {
                        "dynamicRegistration": True,
                        "signatureInformation": {
                            "documentationFormat": ["markdown", "plaintext"],
                            "parameterInformation": {"labelOffsetSupport": True},
                        },
                    },
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True},
                    "documentSymbol": {
                        "dynamicRegistration": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                        "hierarchicalDocumentSymbolSupport": True,
                    },
                    "publishDiagnostics": {"relatedInformation": True},
                },
            },
            "trace": "verbose",
            "processId": os.getpid(),
            "rootPath": repository_absolute_path,
            "rootUri": pathlib.Path(repository_absolute_path).as_uri(),
            "workspaceFolders": [
                {
                    "uri": root_uri,
                    "name": os.path.basename(repository_absolute_path),
                }
            ],
        }
        return initialize_params

    def _start_server(self):
        """
        Starts the Solargraph Language Server for Ruby
        """

        def register_capability_handler(params):
            assert "registrations" in params
            for registration in params["registrations"]:
                if registration["method"] == "workspace/executeCommand":
                    self.initialize_searcher_command_available.set()
                    self.resolve_main_method_available.set()
            return

        def lang_status_handler(params):
            if params.get("type") == "ProjectStatus" and params.get("message") == "OK":
                self.logger.log("Solargraph project has been successfully indexed.", logging.INFO)
                self.service_ready_event.set()
            elif params.get("type") == "ServiceReady" and params.get("message") == "ServiceReady":
                self.logger.log("Solargraph service is ready.", logging.INFO)
                # This is a good sign, but we will wait for the project to be indexed

        def execute_client_command_handler(params):
            return []

        def do_nothing(params):
            return

        def window_log_message(msg):
            message = msg.get("message", "")
            self.logger.log(f"LSP: window/logMessage: {message}", logging.INFO)
            if "Solargraph is ready" in message:
                self.logger.log("Detected 'Solargraph is ready' message.", logging.INFO)
                self.service_ready_event.set()

        self.server.on_request("client/registerCapability", register_capability_handler)
        self.server.on_notification("language/status", lang_status_handler)
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_request("workspace/executeClientCommand", execute_client_command_handler)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)
        self.server.on_notification("language/actionableNotification", do_nothing)

        self.logger.log("Starting solargraph server process", logging.INFO)
        self.server.start()
        initialize_params = self._get_initialize_params(self.repository_root_path)

        self.logger.log(
            "Sending initialize request from LSP client to LSP server and awaiting response",
            logging.INFO,
        )
        self.logger.log(f"Sending init params: {json.dumps(initialize_params, indent=4)}", logging.INFO)
        init_response = self.server.send.initialize(initialize_params)
        self.logger.log(f"Received init response: {init_response}", logging.INFO)
        assert init_response["capabilities"]["textDocumentSync"] == 2  # 2 is Full
        assert "completionProvider" in init_response["capabilities"]
        assert init_response["capabilities"]["completionProvider"] == {
            "resolveProvider": True,
            "triggerCharacters": [".", ":", "@"],
        }
        self.server.notify.initialized({})

        # Wait for server to be ready with timeout, especially important for Bundler environments
        server_ready_timeout = 120.0
        self.logger.log(f"Waiting up to {server_ready_timeout} seconds for Solargraph to become ready...", logging.INFO)

        if self.service_ready_event.wait(timeout=server_ready_timeout):
            self.logger.log("Solargraph is ready and available for requests", logging.INFO)
            self.completions_available.set()
        else:
            self.logger.log(
                f"Timeout waiting for Solargraph to become ready within {server_ready_timeout} seconds, proceeding anyway. "
                "This may indicate slow initialization in Bundler environment or large project indexing.",
                logging.WARNING,
            )
            self.completions_available.set()  # Set completions available even on timeout
