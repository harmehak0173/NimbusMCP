#!/usr/bin/env python3
"""
Weather MCP Server

This server provides weather information through the Model Context Protocol.
It fetches weather data from OpenWeatherMap API and exposes it as MCP resources and tools.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    ServerCapabilities
)
from pydantic import BaseModel


class WeatherData(BaseModel):
    """Weather data model"""
    location: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float
    feels_like: float


class WeatherMCPServer:
    """MCP Server for weather data"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()

        self.server = Server("weather-server")
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available weather resources"""
            return [
                Resource(
                    uri="weather://current",
                    name="Current Weather",
                    description="Get current weather for any location",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read weather resource"""
            if uri == "weather://current":
                return json.dumps({
                    "description": "Current weather resource",
                    "usage": "Use the get_weather tool to fetch current weather data",
                    "example": "get_weather(location='New York')"
                })
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available weather tools"""
            return [
                Tool(
                    name="get_weather",
                    description="Get current weather information for a specific location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name, state/country (e.g., 'New York, NY' or 'London, UK')"
                            },
                            "units": {
                                "type": "string",
                                "enum": ["metric", "imperial", "kelvin"],
                                "default": "metric",
                                "description": "Temperature units (metric=Celsius, imperial=Fahrenheit, kelvin=Kelvin)"
                            }
                        },
                        "required": ["location"]
                    }
                ),
                Tool(
                    name="get_forecast",
                    description="Get 5-day weather forecast for a specific location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name, state/country (e.g., 'New York, NY' or 'London, UK')"
                            },
                            "units": {
                                "type": "string",
                                "enum": ["metric", "imperial", "kelvin"],
                                "default": "metric",
                                "description": "Temperature units"
                            }
                        },
                        "required": ["location"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            if name == "get_weather":
                return await self._get_current_weather(arguments)
            elif name == "get_forecast":
                return await self._get_weather_forecast(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _get_current_weather(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get current weather data"""
        location = arguments.get("location")
        units = arguments.get("units", "metric")
        
        if not self.api_key:
            return [TextContent(
                type="text",
                text="Error: OPENWEATHER_API_KEY environment variable not set"
            )]
        
        try:
            async with httpx.AsyncClient() as client:
                # OpenWeather accepts 'metric' or 'imperial'; Kelvin is default when units is omitted
                api_units = None if units == "kelvin" else units
                params = {
                    "q": location,
                    "appid": self.api_key,
                }
                if api_units:
                    params["units"] = api_units
                
                response = await client.get(f"{self.base_url}/weather", params=params)
                response.raise_for_status()
                
                data = response.json()
                
                weather_info = {
                    "location": f"{data['name']}, {data['sys']['country']}",
                    "temperature": data['main']['temp'],
                    "feels_like": data['main']['feels_like'],
                    "description": data['weather'][0]['description'].title(),
                    "humidity": data['main']['humidity'],
                    "wind_speed": data['wind']['speed'],
                    "pressure": data['main']['pressure'],
                    "visibility": data.get('visibility', 'N/A'),
                    "units": units
                }
                
                # Format the response nicely
                unit_symbol = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
                wind_unit = "m/s" if units in ("metric", "kelvin") else "mph"
                
                formatted_response = f"""Current Weather for {weather_info['location']}:
🌡️ Temperature: {weather_info['temperature']}{unit_symbol} (feels like {weather_info['feels_like']}{unit_symbol})
🌤️ Conditions: {weather_info['description']}
💧 Humidity: {weather_info['humidity']}%
💨 Wind Speed: {weather_info['wind_speed']} {wind_unit}
🔽 Pressure: {weather_info['pressure']} hPa
👁️ Visibility: {weather_info['visibility']} meters"""
                
                return [TextContent(
                    type="text",
                    text=formatted_response
                )]
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return [TextContent(
                    type="text",
                    text=f"Error: Location '{location}' not found. Please check the spelling and try again."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error fetching weather data: {e.response.status_code} - {e.response.text}"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    async def _get_weather_forecast(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get weather forecast data"""
        location = arguments.get("location")
        units = arguments.get("units", "metric")
        
        if not self.api_key:
            return [TextContent(
                type="text",
                text="Error: OPENWEATHER_API_KEY environment variable not set"
            )]
        
        try:
            async with httpx.AsyncClient() as client:
                # OpenWeather accepts 'metric' or 'imperial'; Kelvin is default when units is omitted
                api_units = None if units == "kelvin" else units
                params = {
                    "q": location,
                    "appid": self.api_key,
                }
                if api_units:
                    params["units"] = api_units

                response = await client.get(f"{self.base_url}/forecast", params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Format forecast data
                unit_symbol = "°C" if units == "metric" else "°F" if units == "imperial" else "K"

                forecast_text = f"5-Day Weather Forecast for {data['city']['name']}, {data['city']['country']}:\n\n"

                # Group all entries by date
                by_date: Dict[str, List[Dict[str, Any]]] = {}
                for item in data.get('list', []):
                    dt_txt = item.get('dt_txt', '')
                    date = dt_txt.split(' ')[0] if ' ' in dt_txt else dt_txt
                    by_date.setdefault(date, []).append(item)

                # Sort dates and pick up to 5 days
                dates = sorted(by_date.keys())[:5]

                def pick_representative(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
                    # Prefer 12:00:00 entry if present, else choose middle entry
                    noon = [e for e in entries if e.get('dt_txt', '').endswith('12:00:00')]
                    if noon:
                        return noon[0]
                    return entries[len(entries)//2]

                for date in dates:
                    entries = by_date[date]
                    forecast = pick_representative(entries)
                    temp = forecast['main']['temp']
                    desc = forecast['weather'][0]['description'].title()
                    humidity = forecast['main']['humidity']
                    forecast_text += f"📅 {date}: {temp}{unit_symbol}, {desc}, Humidity: {humidity}%\n"
                
                return [TextContent(
                    type="text",
                    text=forecast_text
                )]
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return [TextContent(
                    type="text",
                    text=f"Error: Location '{location}' not found. Please check the spelling and try again."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error fetching forecast data: {e.response.status_code} - {e.response.text}"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="weather-server",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(),
                ),
            )


async def main():
    """Main entry point"""
    server = WeatherMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
