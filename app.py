from shiny import App, render, ui, reactive

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_action_button(
            "set_websocket",
            "Force Websocket & Reload",
            class_="btn-warning"
        ),
        ui.br(),
        ui.br(),
        ui.input_action_button(
            "set_xhr_streaming",
            "Force XHR-Streaming & Reload",
            class_="btn-info"
        ),
        ui.br(),
        ui.br(),
        ui.p("Click a button above to:"),
        ui.tags.ol(
            ui.tags.li("Set localStorage['shiny.whitelist'] to restrict the transport method"),
            ui.tags.li("Reload the page to force the selected transport"),
        ),
        ui.br(),
        ui.p(
            "If the forced transport is broken, the app will not load correctly after reload.",
            class_="text-muted"
        ),
    ),
    ui.card(
        ui.card_header("Current Status"),
        ui.output_ui("status_info"),
    ),
    ui.card(
        ui.card_header("Transport Information"),
        ui.output_ui("transport_info"),
    ),
    ui.card(
        ui.card_header("Console Monitoring"),
        ui.output_ui("console_log_display"),
    ),
    ui.card(
        ui.card_header("Test Content"),
        ui.p("This is a test Shiny app to verify websocket functionality."),
        ui.input_text("test_input", "Type something:", value="Hello, Shiny!"),
        ui.output_text("test_output"),
    ),
    title="Websocket Connectivity Test"
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.set_websocket)
    def _():
        # JavaScript code to set localStorage and reload page
        js_code = """
        // Set the shiny whitelist to force websocket usage
        window.localStorage["shiny.whitelist"] = '["websocket"]';

        // Reload the page to apply the setting
        window.location.reload();
        """
        ui.insert_ui(
            selector="body",
            ui=ui.tags.script(js_code),
            where="beforeEnd"
        )

    @reactive.effect
    @reactive.event(input.set_xhr_streaming)
    def _():
        # JavaScript code to set localStorage to xhr-streaming and reload page
        js_code = """
        // Set the shiny whitelist to force xhr-streaming usage
        window.localStorage["shiny.whitelist"] = '["xhr-streaming"]';

        // Reload the page to apply the setting
        window.location.reload();
        """
        ui.insert_ui(
            selector="body",
            ui=ui.tags.script(js_code),
            where="beforeEnd"
        )

    @render.ui
    def status_info():
        # JavaScript to check current localStorage setting
        check_js = """
        function checkWebsocketSetting() {
            const whitelist = window.localStorage["shiny.whitelist"];
            const statusDiv = document.getElementById("websocket-status");
            if (statusDiv) {
                if (whitelist === '["xhr-streaming"]') {
                    statusDiv.innerHTML = '<div class="alert alert-success">XHR-streaming whitelist is enabled and app works correctly</div>';
                } else if (whitelist === '["websocket"]') {
                    statusDiv.innerHTML = '<div class="alert alert-success">Websocket whitelist is enabled and app works correctly</div>';
                } else {
                    statusDiv.innerHTML = '<div class="alert alert-info">Websocket whitelist is NOT set (default behavior)</div>';
                }
            }
        }
        // Run the check after a short delay to ensure DOM is ready
        setTimeout(checkWebsocketSetting, 100);
        """

        return ui.div(
            ui.div("Checking...", id="websocket-status"),
            ui.tags.script(check_js),
        )

    @render.ui
    def transport_info():
        # JavaScript to detect the current transport mechanism
        transport_js = """
        function detectTransport() {
            const transportDiv = document.getElementById("transport-status");
            if (!transportDiv) return;

            // Function to check transport with retries
            function checkTransport(attempts = 0) {
                if (attempts > 20) {
                    transportDiv.innerHTML = '<div class="alert alert-warning">Could not detect transport (Shiny may still be initializing)</div>';
                    return;
                }

                try {
                    // Check if Shiny object exists and has socket
                    if (window.Shiny && window.Shiny.shinyapp && window.Shiny.shinyapp.config) {
                        const config = window.Shiny.shinyapp.config;
                        let transportInfo = '';
                        let alertClass = 'alert-info';

                        // Check various ways to determine transport
                        if (window.Shiny.shinyapp.$socket) {
                            const socket = window.Shiny.shinyapp.$socket;

                            // Check if it's using websockets
                            if (socket.transport && socket.transport.name) {
                                const transportName = socket.transport.name;
                                transportInfo = `Active Transport: <strong>${transportName}</strong>`;

                                if (transportName === 'websocket') {
                                    alertClass = 'alert-success';
                                } else {
                                    alertClass = 'alert-warning';
                                }
                            } else if (socket.socket && socket.socket.transport) {
                                const transportName = socket.socket.transport.name;
                                transportInfo = `Active Transport: <strong>${transportName}</strong>`;

                                if (transportName === 'websocket') {
                                    alertClass = 'alert-success';
                                } else {
                                    alertClass = 'alert-warning';
                                }
                            } else {
                                // Try to detect based on socket properties
                                if (socket.socket && socket.socket.readyState !== undefined) {
                                    transportInfo = 'Active Transport: <strong>websocket</strong> (detected via WebSocket API)';
                                    alertClass = 'alert-success';
                                } else {
                                    transportInfo = 'Active Transport: <strong>polling/xhr</strong> (fallback detected)';
                                    alertClass = 'alert-warning';
                                }
                            }
                        } else {
                            transportInfo = 'Transport: <strong>Shiny socket not yet available</strong>';
                        }

                        // Add whitelist info
                        const whitelist = window.localStorage["shiny.whitelist"];
                        let whitelistInfo = '';
                        if (whitelist === '["websocket"]') {
                            whitelistInfo = '<br><small>Connection forced to websocket-only mode</small>';
                        } else if (whitelist === '["xhr-streaming"]') {
                            whitelistInfo = '<br><small>Connection forced to xhr-streaming mode</small>';
                        } else {
                            whitelistInfo = '<br><small>Using automatic transport selection</small>';
                        }

                        transportDiv.innerHTML = `<div class="alert ${alertClass}">${transportInfo}${whitelistInfo}</div>`;
                    } else {
                        // Shiny not ready yet, retry
                        setTimeout(() => checkTransport(attempts + 1), 200);
                    }
                } catch (error) {
                    setTimeout(() => checkTransport(attempts + 1), 200);
                }
            }

            checkTransport();
        }

        // Run detection after Shiny loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => setTimeout(detectTransport, 500));
        } else {
            setTimeout(detectTransport, 500);
        }

        // Also re-run when Shiny connects
        $(document).on('shiny:connected', function() {
            setTimeout(detectTransport, 100);
        });
        """

        return ui.div(
            ui.div("Detecting transport...", id="transport-status"),
            ui.tags.script(transport_js),
        )

    @render.ui
    def console_log_display():
        console_js = """
        // Initialize captured logs store (idempotent — survives Shiny output re-renders)
        if (!window.capturedLogs) {
            window.capturedLogs = [];

            const originalLog = console.log;
            const originalWarn = console.warn;
            const originalError = console.error;

            function capture(level, args) {
                const msg = Array.from(args).map(function(a) {
                    return (typeof a === 'object') ? JSON.stringify(a) : String(a);
                }).join(' ');
                window.capturedLogs.push({ level: level, msg: msg, time: new Date().toISOString() });
                updateConsoleDisplay();
            }

            console.log = function() { capture('log', arguments); originalLog.apply(console, arguments); };
            console.warn = function() { capture('warn', arguments); originalWarn.apply(console, arguments); };
            console.error = function() { capture('error', arguments); originalError.apply(console, arguments); };
        }

        function updateConsoleDisplay() {
            const el = document.getElementById("console-log-output");
            if (!el) return;
            const total = window.capturedLogs.length;
            const disconnects = window.capturedLogs.filter(function(e) {
                return e.msg.indexOf("Disconnect detected") !== -1;
            });
            let html = '<p>Total captured messages: <strong>' + total + '</strong></p>';
            if (disconnects.length > 0) {
                html += '<div class="alert alert-danger">Disconnect detected messages (' + disconnects.length + '):<ul>';
                disconnects.forEach(function(e) {
                    html += '<li>' + e.time + ': ' + e.msg + '</li>';
                });
                html += '</ul></div>';
            } else {
                html += '<div class="alert alert-success">No &quot;Disconnect detected&quot; messages captured</div>';
            }
            el.innerHTML = html;
        }

        // Initial render
        setTimeout(updateConsoleDisplay, 200);
        """

        return ui.div(
            ui.div("Console monitoring initializing...", id="console-log-output"),
            ui.tags.script(console_js),
        )

    @render.text
    def test_output():
        return f"You typed: {input.test_input()}"


app = App(app_ui, server)
