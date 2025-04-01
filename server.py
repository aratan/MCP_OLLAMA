from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")


@mcp.tool()
def get_email_inbox(email_address: str):
    """Get the email inbox of a user"""
    # TODO Conectar a alguna api real, por ejemplo Gmail API
    return [
        {
            "from": "soporte@gmail.com",
            "to": email_address,
            "subject": "ayuda",
            "body": "No puedo entrar a mi cuenta",
        }
    ]


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def sales_report(month: int) -> dict[str, Any]:
    """Genera un reporte de ventas para un mes especifico"""
    # TODO consultar a la base de datos real
    return {
        "total_sales": 100000,
        "total_orders": 300,
        "total_customers": 4000,
        "best_client": "Jhon Doe",
    }


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting MCP server...")
    mcp.run(transport="stdio")
