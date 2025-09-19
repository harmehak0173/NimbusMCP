#!/usr/bin/env python3
"""
LLM Weather Client

This client demonstrates how to use an LLM with MCP to fetch and analyze weather data.
It connects to the weather MCP server and uses an LLM to provide intelligent weather insights.
"""

import asyncio
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
import httpx


class WeatherLLMClient:
    """LLM client that uses MCP for weather data"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
    
    async def connect_to_mcp_server(self):
        """Connect to the weather MCP server"""
        try:
            self._exit_stack = AsyncExitStack()

            # Prepare stdio server parameters to spawn the server
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["weather_mcp_server.py"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )

            # Open stdio transport
            read_stream, write_stream = await self._exit_stack.enter_async_context(stdio_client(server_params))

            # Create MCP client session
            self.session = await self._exit_stack.enter_async_context(ClientSession(read_stream, write_stream))

            # Initialize the session
            await self.session.initialize()

            print("✅ Connected to weather MCP server")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self._exit_stack is not None:
            try:
                await self._exit_stack.aclose()
            finally:
                self._exit_stack = None
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        tools = await self.session.list_tools()
        return [tool.model_dump() for tool in tools.tools]
    
    async def get_weather(self, location: str, units: str = "metric") -> str:
        """Get current weather for a location"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(
                "get_weather",
                {"location": location, "units": units}
            )
            
            if result.content:
                return result.content[0].text
            else:
                return "No weather data received"
                
        except Exception as e:
            return f"Error getting weather: {e}"
    
    async def get_forecast(self, location: str, units: str = "metric") -> str:
        """Get weather forecast for a location"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(
                "get_forecast",
                {"location": location, "units": units}
            )
            
            if result.content:
                return result.content[0].text
            else:
                return "No forecast data received"
                
        except Exception as e:
            return f"Error getting forecast: {e}"
    
    def analyze_weather_with_llm(self, weather_data: str, user_query: str) -> str:
        """
        Synchronous wrapper preserved for compatibility. Attempts to run async
        analysis; on failure, returns enhanced rule-based analysis.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Cannot run new event loop here; fall back to rule-based
            return self._rule_based_analysis(weather_data, user_query)
        try:
            return asyncio.run(self.analyze_weather_with_llm_async(weather_data, user_query))
        except Exception:
            return self._rule_based_analysis(weather_data, user_query)

    async def analyze_weather_with_llm_async(self, weather_data: str, user_query: str) -> str:
        """Async analysis preferring OpenAI, then Hugging Face Inference API, then Ollama, then rule-based."""
        # 1) Try OpenAI if available
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        if openai_key:
            analysis = await self._analyze_with_openai(openai_key, openai_model, weather_data, user_query)
            if analysis:
                return analysis

        # 2) Try Hugging Face Inference API if token is available (often free tier)
        hf_token = os.getenv("HF_API_TOKEN", "").strip()
        hf_model = os.getenv("HF_MODEL", "HuggingFaceH4/zephyr-7b-beta").strip()
        if hf_token:
            analysis = await self._analyze_with_hf(hf_token, hf_model, weather_data, user_query)
            if analysis:
                return analysis

        # 3) Try Ollama locally (can be disabled by setting OLLAMA_HOST="")
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        if ollama_host:
            analysis = await self._analyze_with_ollama(ollama_host, ollama_model, weather_data, user_query)
            if analysis:
                return analysis

        # 4) Fallback to rules
        return self._rule_based_analysis(weather_data, user_query)

    def _rule_based_analysis(self, weather_data: str, user_query: str) -> str:
        """Improved heuristic analysis when LLM is unavailable."""
        lines = weather_data.split('\n')
        get = lambda key: next((l for l in lines if key in l), "")

        # Parse values
        temp = None
        try:
            tline = get('Temperature:')
            if tline:
                tpart = tline.split('Temperature:')[1].split('(')[0].strip()
                temp = float(tpart.split('°')[0])
        except Exception:
            pass

        feels = None
        try:
            if tline and '(' in tline:
                fpart = tline.split('feels like')[-1].rstrip(')').strip()
                feels = float(fpart.split('°')[0])
        except Exception:
            pass

        desc = get('Conditions:').split(':',1)[-1].strip().lower()
        hum = None
        try:
            hline = get('Humidity:')
            if hline:
                hum = int(hline.split(':')[1].strip('% '))
        except Exception:
            pass

        wind = None
        try:
            wline = get('Wind Speed:')
            if wline:
                wind = float(wline.split(':')[1].split()[0])
        except Exception:
            pass

        vis = None
        try:
            vline = get('Visibility:')
            if vline:
                vis = int(''.join(ch for ch in vline if ch.isdigit()))
        except Exception:
            pass

        tips: List[str] = []

        # Temperature-based clothing
        if temp is not None:
            if temp <= 0:
                tips.append("🥶 Very cold. Wear a heavy coat, gloves, and a hat.")
            elif temp <= 10:
                tips.append("🧥 Chilly. A warm jacket and layers are recommended.")
            elif temp >= 30:
                tips.append("🔥 Hot. Stay hydrated, wear light clothing, and limit midday sun.")
            elif temp >= 22:
                tips.append("🌞 Warm and comfortable. T‑shirt or light layers are fine.")
            else:
                tips.append("🌤️ Mild. A light layer should be enough.")

        # Feels-like adjustment
        if temp is not None and feels is not None:
            delta = feels - temp
            if delta <= -3:
                tips.append("↘️ It feels colder than the actual temperature—add an extra layer.")
            elif delta >= 3:
                tips.append("↗️ It feels warmer than the actual temperature—dress lightly.")

        # Precipitation
        if any(k in desc for k in ["rain", "drizzle", "thunder", "shower"]):
            tips.append("☔ Rain expected. Carry an umbrella or waterproof layer.")
        elif "snow" in desc:
            tips.append("❄️ Snowy conditions. Wear insulated boots with good traction.")

        # Humidity comfort
        if hum is not None:
            if hum >= 80:
                tips.append("💧 Very humid—expect it to feel muggy. Stay hydrated.")
            elif hum <= 30:
                tips.append("💨 Dry air—consider moisturizer and stay hydrated.")

        # Wind advisories
        if wind is not None:
            if wind >= 10:
                tips.append("💨 Breezy to windy—secure hats/light items and consider a windbreaker.")
            if wind >= 17:
                tips.append("🌬️ Strong winds—extra caution for outdoor activities.")

        # Visibility
        if vis is not None and vis < 3000:
            tips.append("👁️ Low visibility—take care if driving.")

        # Condition summary
        if desc:
            tips.append(f"ℹ️ Conditions: {desc.capitalize()}.")

        return "\n".join(dict.fromkeys(tips))  # dedupe while preserving order

    async def _analyze_with_ollama(self, host: str, model: str, weather_data: str, user_query: str) -> Optional[str]:
        """Use local Ollama chat API to analyze weather. Returns None on failure."""
        try:
            # Health check
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Quick ping to root
                try:
                    await client.get(f"{host}/api/tags")
                except Exception:
                    return None

                system_prompt = (
                    "You are a helpful weather expert assistant. Based on the provided weather report, "
                    "answer the user's question with concise, actionable advice. If clothing is relevant, "
                    "give practical recommendations. Keep it to 2-4 short sentences."
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Weather report:\n{weather_data}\n\nUser question: {user_query}"},
                ]

                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                }

                resp = await client.post(f"{host}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Ollama chat format: { 'message': {'role': 'assistant', 'content': '...'}, ... }
                msg = data.get("message", {}).get("content")
                if isinstance(msg, str) and msg.strip():
                    return msg.strip()
                return None
        except Exception:
            return None

    async def _analyze_with_hf(self, api_token: str, model: str, weather_data: str, user_query: str) -> Optional[str]:
        """Use Hugging Face Inference API for text generation. Returns None on failure."""
        try:
            # Simple instruction-style prompt for instruction-tuned models
            prompt = (
                "You are a helpful weather expert assistant. Based on the provided weather report, "
                "answer the user's question with concise, actionable advice in 2-4 short sentences. "
                "Vary your wording naturally, and include clothing or safety tips when relevant.\n\n"
                f"Weather report:\n{weather_data}\n\nUser question: {user_query}\n\nAnswer:"
            )

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 180,
                    "temperature": 0.7,
                    "return_full_text": False,
                },
                "options": {"wait_for_model": True},
            }

            url = f"https://api-inference.huggingface.co/models/{model}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code >= 400:
                    return None
                data = resp.json()
                # Responses can be list of dicts with 'generated_text' or dict with 'error'
                if isinstance(data, list) and data:
                    gen = data[0].get("generated_text")
                    if isinstance(gen, str) and gen.strip():
                        return gen.strip()
                return None
        except Exception:
            return None

    async def _analyze_with_openai(self, api_key: str, model: str, weather_data: str, user_query: str) -> Optional[str]:
        """Use OpenAI Chat Completions API to analyze weather. Returns None on failure."""
        try:
            system_prompt = (
                "You are a helpful weather expert assistant. Based on the provided weather report, "
                "answer the user's question with concise, actionable advice. If clothing is relevant, "
                "give practical recommendations. Keep it to 2-4 short sentences. Vary your wording naturally."
            )

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Weather report:\n{weather_data}\n\nUser question: {user_query}"},
                ],
                "temperature": 0.7,
            }

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                if resp.status_code >= 400:
                    return None
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return None
                msg = choices[0].get("message", {}).get("content")
                if isinstance(msg, str) and msg.strip():
                    return msg.strip()
                return None
        except Exception:
            return None
    
    async def chat_about_weather(self):
        """Interactive loop that always asks for a location selection, fetches, shows results, and repeats."""
        print("\n🌤️ Welcome to the Weather LLM Assistant!")
        print("Select a location by number or enter a custom one. Type 'quit' to exit.\n")

        favorites = self._get_favorite_locations()
        if not favorites:
            favorites = [
                "London, UK",
                "New York, US",
                "Tokyo, JP",
                "Sydney, AU",
            ]

        while True:
            try:
                location = self._choose_location_from_menu(favorites)
                if not location:
                    print("👋 Goodbye!")
                    break

                print(f"\n🔍 Getting weather for {location}...")
                weather_data = await self.get_weather(location)
                analysis = await self.analyze_weather_with_llm_async(weather_data, f"Weather for {location}")
                print(f"\nWeather Assistant:\n{weather_data}\n\n🤖 Analysis: {analysis}\n")

                # Immediately loop back to select another location
                continue

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                # Loop back to selection on error as well
                continue
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from user input (simple implementation)"""
        # Look for common location patterns
        words = text.split()
        
        # Look for "in [location]" or "for [location]"
        for i, word in enumerate(words):
            if word.lower() in ['in', 'for', 'at'] and i + 1 < len(words):
                # Take the next word(s) as location
                location_parts = []
                for j in range(i + 1, len(words)):
                    if words[j].lower() in ['weather', 'forecast', 'temperature']:
                        break
                    location_parts.append(words[j])
                
                if location_parts:
                    return ' '.join(location_parts).rstrip('?.,!')
        
        return None

    def _get_favorite_locations(self) -> List[str]:
        """Return favorite locations from env FAVORITE_LOCATIONS (comma-separated)."""
        raw = os.getenv("FAVORITE_LOCATIONS", "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _choose_location_from_menu(self, favorites: List[str]) -> Optional[str]:
        """Prompt a numbered menu to choose a location, or allow custom entry."""
        while True:
            print("Select a location:")
            for idx, loc in enumerate(favorites, start=1):
                print(f"  {idx}) {loc}")
            print("  0) Enter another location")

            choice = input("Your choice (number or location): ").strip()
            if choice.lower() in ["quit", "exit", "bye"]:
                return None
            
            # numeric selection
            if choice.isdigit():
                num = int(choice)
                if num == 0:
                    # custom prompt
                    custom = input("Enter location (e.g., 'Paris, FR'): ").strip()
                    if custom:
                        return custom
                    continue
                if 1 <= num <= len(favorites):
                    return favorites[num - 1]
                print("Invalid number. Please try again.\n")
                continue

            # free text treated as location
            if choice:
                return choice
            
            print("Please enter a selection or a location.\n")


async def main():
    """Main entry point"""
    client = WeatherLLMClient()
    
    try:
        # Connect to MCP server
        if not await client.connect_to_mcp_server():
            return
        
        # List available tools
        print("📋 Available weather tools:")
        tools = await client.list_available_tools()
        for tool in tools:
            print(f"  • {tool['name']}: {tool['description']}")
        
        # Start interactive chat
        await client.chat_about_weather()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
