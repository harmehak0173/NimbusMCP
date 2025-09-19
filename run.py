#!/usr/bin/env python3
"""
Simple launcher for the Weather LLM MCP Project
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm_weather_client import WeatherLLMClient


async def main():
    """Main launcher function"""
    print("🌤️ Weather LLM Assistant")
    print("=" * 30)

    parser = argparse.ArgumentParser(description="Weather LLM Assistant")
    parser.add_argument("--location", "-l", help="Location to fetch weather for (e.g., 'London, UK')")
    parser.add_argument("--units", "-u", choices=["metric", "imperial", "kelvin"], default=os.getenv("DEFAULT_UNITS", "metric"), help="Units for temperature and wind")
    parser.add_argument("--forecast", "-f", action="store_true", help="Get 5-day forecast instead of current weather")
    parser.add_argument("--no-interactive", action="store_true", help="Run non-interactively and exit after printing results")

    args = parser.parse_args()

    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ Configuration file (.env) not found!")
        print("   Please run 'python setup.py' first to set up the project.")
        return

    # Check if API key is configured
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ OpenWeatherMap API key not configured!")
        print("   Please:")
        print("   1. Get a free API key from: https://openweathermap.org/api")
        print("   2. Edit the .env file and add your API key")
        print("   3. Run this script again")
        return

    # Determine interactive mode
    interactive = not args.no_interactive

    client = WeatherLLMClient()

    try:
        if not await client.connect_to_mcp_server():
            print("❌ Failed to start the weather assistant")
            print("   Try running 'python test_system.py' to diagnose issues")
            return

        # Interactive loop
        if interactive:
            while True:
                try:
                    default_loc = os.getenv("DEFAULT_LOCATION", "").strip()
                    user_input = input("Enter location (e.g., 'London, UK') (type 'quit' to exit): ").strip()
                    if user_input.lower() in {"quit", "exit", "q"}:
                        break
                    location = user_input or (default_loc or None)
                    if not location:
                        print("❌ No location provided. Use --location, set DEFAULT_LOCATION in .env, or enter one when prompted.\n")
                        continue

                    # Choice current vs forecast
                    forecast_choice = args.forecast
                    if not args.forecast:
                        print("\nWhat would you like to see?")
                        print("  1) Current weather")
                        print("  2) 5-day forecast")
                        choice = input("Choose 1 or 2: ").strip()
                        forecast_choice = (choice == "2")

                    # Fetch and display
                    if forecast_choice:
                        print(f"🔍 Getting forecast for {location}...")
                        text = await client.get_forecast(location, units=args.units)
                        print(text)
                    else:
                        print(f"🔍 Getting weather for {location}...")
                        weather_text = await client.get_weather(location, units=args.units)
                        analysis = client.analyze_weather_with_llm(weather_text, f"Weather for {location}")
                        print(f"{weather_text}\n\n🤖 Analysis: {analysis}")

                    # loop back to prompt again
                    continue
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
            return

        # Non-interactive single run
        location = args.location or os.getenv("DEFAULT_LOCATION")
        if not location:
            print("❌ No location provided. Use --location or set DEFAULT_LOCATION in .env")
            return
        if args.forecast:
            print(f"🔍 Getting forecast for {location}...")
            text = await client.get_forecast(location, units=args.units)
            print(text)
        else:
            print(f"🔍 Getting weather for {location}...")
            weather_text = await client.get_weather(location, units=args.units)
            analysis = client.analyze_weather_with_llm(weather_text, f"Weather for {location}")
            print(f"{weather_text}\n\n🤖 Analysis: {analysis}")
        return

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
