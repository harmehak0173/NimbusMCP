import json
import mcp.types as t
from mcp.server import Server
from mcp.server.models import InitializationOptions

print('ServerCapabilities model_fields keys:')
print(list(getattr(t.ServerCapabilities, 'model_fields', {}).keys()))

s = Server('x')
try:
    caps = s.get_capabilities(notification_options=None, experimental_capabilities=None)
    print('auto caps keys:', list(caps.model_dump().keys()))
    print('auto caps:', caps.model_dump())
except Exception as e:
    print('error get_capabilities:', e)
