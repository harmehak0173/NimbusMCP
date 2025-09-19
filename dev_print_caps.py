from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as t
import inspect

s = Server('x')
print('get_capabilities signature:', inspect.signature(Server.get_capabilities))
try:
    caps = s.get_capabilities(notification_options=None, experimental_capabilities=None)
    print('caps:', caps)
    print('caps dict:', caps.model_dump())
except Exception as e:
    print('error calling get_capabilities with 2 None args:', e)

try:
    caps2 = s.get_capabilities()
    print('caps2:', caps2)
    print('caps2 dict:', caps2.model_dump())
except Exception as e:
    print('error calling get_capabilities with 0 args:', e)

print('InitializationOptions annotations:', getattr(InitializationOptions, '__annotations__', {}))
