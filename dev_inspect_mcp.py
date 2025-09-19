import inspect
import mcp
from mcp.client import stdio as cs
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as t

print('mcp module:', mcp)
print('mcp version:', getattr(mcp, '__version__', 'unknown'))
print('stdio_client signature:', inspect.signature(cs.stdio_client))
print('Has StdioServerParameters on mcp?', hasattr(mcp, 'StdioServerParameters'))
print('StdioServerParameters type:', getattr(cs, 'StdioServerParameters', None))
print('Server.get_capabilities signature:', inspect.signature(Server.get_capabilities))
print('InitializationOptions annotations:', getattr(InitializationOptions, '__annotations__', {}))
print('ServerCapabilities type:', getattr(t, 'ServerCapabilities', None))
