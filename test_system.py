#!/usr/bin/env python3
"""
Test script for the Weather LLM MCP system
"""

import asyncio
import os
import sys
from llm_weather_client import WeatherLLMClient


async def test_mcp_connection():
    """Test MCP server connection and basic functionality"""
    print("🧪 Testing Weather LLM MCP System")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("❌ OPENWEATHER_API_KEY not found in environment")
        print("   Please copy .env.example to .env and add your API key")
        return False
    
    print("✅ API key found")
    
    client = WeatherLLMClient()
    
    try:
        # Test MCP server connection
        print("\n🔌 Testing MCP server connection...")
        if not await client.connect_to_mcp_server():
            print("❌ Failed to connect to MCP server")
            return False
        
        print("✅ MCP server connected successfully")
        
        # Test listing tools
        print("\n📋 Testing tool listing...")
        tools = await client.list_available_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   • {tool['name']}: {tool['description']}")
        
        # Test weather fetching
        print("\n🌤️ Testing weather fetching...")
        test_location = "London, UK"
        weather_data = await client.get_weather(test_location)
        
        if "Error" in weather_data:
            print(f"❌ Weather fetch failed: {weather_data}")
            return False
        
        print(f"✅ Weather data retrieved for {test_location}")
        print(f"   Preview: {weather_data[:100]}...")
        
        # Test forecast fetching
        print("\n📅 Testing forecast fetching...")
        forecast_data = await client.get_forecast(test_location)
        
        if "Error" in forecast_data:
            print(f"❌ Forecast fetch failed: {forecast_data}")
            return False
        
        print(f"✅ Forecast data retrieved for {test_location}")
        print(f"   Preview: {forecast_data[:100]}...")
        
        # Test LLM analysis
        print("\n🤖 Testing LLM analysis...")
        test_query = "Should I wear a jacket?"
        analysis = client.analyze_weather_with_llm(weather_data, test_query)
        print(f"✅ Analysis generated: {analysis}")
        
        print("\n🎉 All tests passed! The system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        await client.disconnect()


async def run_interactive_demo():
    """Run a quick interactive demo"""
    print("\n" + "=" * 50)
    print("🎮 Interactive Demo")
    print("=" * 50)
    
    client = WeatherLLMClient()
    
    try:
        if not await client.connect_to_mcp_server():
            return
        
        print("Enter a location to get weather for (or 'skip' to skip demo):")
        location = input("Location: ").strip()
        
        if location.lower() != 'skip' and location:
            print(f"\n🔍 Getting weather for {location}...")
            weather_data = await client.get_weather(location)
            print(f"\n{weather_data}")
            
            # Simple analysis
            analysis = client.analyze_weather_with_llm(weather_data, "What should I know about this weather?")
            print(f"\n🤖 Analysis: {analysis}")
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        await client.disconnect()


async def main():
    """Main test function"""
    print("Weather LLM MCP System Test Suite")
    print("=" * 50)
    
    # Run basic tests
    success = await test_mcp_connection()
    
    if success:
        # Run interactive demo if tests pass
        demo = input("\nWould you like to run an interactive demo? (y/n): ").strip().lower()
        if demo in ['y', 'yes']:
            await run_interactive_demo()
    
    print("\n" + "=" * 50)
    print("Test complete!")
    
    if success:
        print("🎉 Your Weather LLM MCP system is ready to use!")
        print("   Run 'python llm_weather_client.py' to start the interactive chat.")
    else:
        print("❌ Please fix the issues above before using the system.")


if __name__ == "__main__":
    asyncio.run(main())
