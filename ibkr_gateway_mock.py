"""
Minimal mock IBKR Gateway server for development/testing when real Gateway is unavailable.
Accepts connections on port 4003 and responds to basic IB API protocol messages.
"""

import socket
import struct
import threading
import time
import logging

logger = logging.getLogger(__name__)

class MockIBGateway:
    def __init__(self, host="0.0.0.0", port=4003):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.thread = None
        
    def start(self):
        """Start mock gateway in background thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Mock IBKR Gateway started on {self.host}:{self.port}")
        
    def _run(self):
        """Main server loop"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    threading.Thread(target=self._handle_client, args=(client_socket, addr), daemon=True).start()
                except Exception as e:
                    if self.running:
                        logger.debug(f"Accept error: {e}")
                        
        except Exception as e:
            logger.error(f"Mock Gateway error: {e}")
        finally:
            self.stop()
            
    def _handle_client(self, client_socket, addr):
        """Handle individual client connection"""
        try:
            logger.debug(f"Client connected: {addr}")
            
            # Keep connection alive and respond to basic messages
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                        
                    # Basic response - IB API uses length-prefixed messages
                    # For now, just acknowledge receipt
                    response = b"OK"
                    client_socket.send(response)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"Client handler error: {e}")
                    break
                    
        finally:
            try:
                client_socket.close()
            except:
                pass
            logger.debug(f"Client disconnected: {addr}")
            
    def stop(self):
        """Stop mock gateway"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info("Mock IBKR Gateway stopped")

# Global instance
_mock_gateway = None

def start_mock_gateway(host="0.0.0.0", port=4003):
    """Start mock IBKR Gateway if real one is unavailable"""
    global _mock_gateway
    if _mock_gateway is None:
        _mock_gateway = MockIBGateway(host, port)
        _mock_gateway.start()
    return _mock_gateway

def stop_mock_gateway():
    """Stop mock gateway"""
    global _mock_gateway
    if _mock_gateway:
        _mock_gateway.stop()
        _mock_gateway = None
