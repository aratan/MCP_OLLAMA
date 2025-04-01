import asyncio
import sys
from typing import Optional
from contextlib import AsyncExitStack
import aiohttp

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.ollama_url = "http://localhost:11434/api/chat"
        self.current_model = "llama3.2:3b"  # Modelo por defecto

    async def connect_to_server(self, server_script_path: str):
        """Conectar al servidor MCP"""
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        
        if self.session:
            await self.session.initialize()
            response = await self.session.list_tools()
            tools = response.tools
            print("\nConectado, herramientas disponibles:", [tool.name for tool in tools])

    async def call_ollama(self, messages: list) -> str:
        """Llamar a la API de Ollama"""
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                self.ollama_url,
                json={
                    "model": self.current_model,
                    "messages": messages,
                    "stream": False
                }
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise ConnectionError(f"Ollama API error: {error}")
                
                data = await response.json()
                return data["message"]["content"]

    async def process_query(self, query: str) -> str:
        """Procesar consulta usando Ollama y herramientas MCP"""
        messages = [{"role": "user", "content": query}]

        if not self.session:
            raise ValueError("No conectado al servidor")

        # Obtener herramientas disponibles
        response = await self.session.list_tools()
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

        # Primera llamada a Ollama
        initial_response = await self.call_ollama(messages)
        
        # Aquí puedes añadir lógica para manejar herramientas si es necesario
        # Ejemplo básico:
        if "[LLAMAR-HERRAMIENTA]" in initial_response:
            tool_name = "mi_herramienta"  # Extraer esto dinámicamente en implementación real
            tool_result = await self.session.call_tool(tool_name, {})
            return f"{initial_response}\n\nResultado de herramienta:\n{tool_result.content}"
        
        return initial_response

    async def chat_loop(self):
        """Bucle de chat interactivo"""
        print("\nCliente MCP-Ollama Iniciado!")
        print(f"Modelo actual: {self.current_model}")
        print("Escribe tus consultas o 'quit' para salir.\n")

        while True:
            try:
                query = await asyncio.to_thread(input, "> ")
                query = query.strip()

                if not query:
                    continue
                
                if query.lower() == "quit":
                    break
                elif query.lower().startswith("/model "):
                    self.current_model = query[7:].strip()
                    print(f"Modelo cambiado a: {self.current_model}")
                    continue

                response = await self.process_query(query)
                print(f"\n{response}\n")

            except Exception as e:
                print(f"\nError: {str(e)}\n")

    async def cleanup(self):
        """Liberar recursos"""
        await self.exit_stack.aclose()
        if self.session:
            await self.session.close()

async def main():
    if len(sys.argv) < 2:
        print("Uso: python client.py <ruta_al_script_del_servidor>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    except Exception as e:
        print(f"Error crítico: {str(e)}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())