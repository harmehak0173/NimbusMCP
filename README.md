# Nimbus Weather MCP Assistant

An interactive, MCP-powered weather assistant in Python. It pairs a Model Context Protocol (MCP) server that fetches OpenWeather data with a client that analyzes and presents current conditions or a 5‑day forecast. The CLI loops so you can query multiple locations without restarting.

## 🌟 Features

- **MCP Weather Server**: Tools for current conditions and 5‑day forecast via MCP.
- **LLM Analysis Pipeline**: OpenAI → Hugging Face Inference API → local Ollama → rule‑based fallback for varied, concise advice.
- **Interactive Looping CLI**: Prompted location entry and choice between current vs 5‑day forecast; keeps running until you type `quit`.
- **Accurate 5‑Day Grouping**: Forecast groups entries per day (prefers noon) to ensure five distinct days.
- **Flexible Units**: Metric, imperial, and Kelvin.

## 🏗️ Architecture

```
┌─────────────────┐    MCP Protocol    ┌──────────────────┐    HTTP API    ┌─────────────────┐
│   LLM Client    │◄──────────────────►│  Weather MCP     │◄──────────────►│ OpenWeatherMap  │
│                 │                    │     Server       │                │      API        │
│ - Chat Interface│                    │ - Weather Tools  │                │                 │
│ - LLM Analysis  │                    │ - Data Formatting│                │                 │
└─────────────────┘                    └──────────────────┘                └─────────────────┘
```

## 📋 Prerequisites

1. **Python 3.8+**
2. **OpenWeatherMap API Key** (free): Get one at [openweathermap.org/api](https://openweathermap.org/api)
3. **Optional**: OpenAI API Key for advanced LLM features

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd C:\Users\harme\CascadeProjects\llm-weather-mcp
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Copy the example environment file and add your API keys:

```bash
copy .env.example .env
```

Edit `.env` and add your OpenWeatherMap API key:
```
OPENWEATHER_API_KEY=your_actual_api_key_here

# Optional: LLM analysis keys
# OPENAI_API_KEY=sk-...
# HF_API_TOKEN=hf_...
# OLLAMA_HOST=http://localhost:11434
```

### 4. Run the Weather Assistant

```bash
python run.py
```

You’ll be prompted for a location and whether you want current weather or the 5‑day forecast. The app will keep prompting until you type `quit`.

## 🔧 Components

### Weather MCP Server (`weather_mcp_server.py`)

The MCP server provides two main tools:

- **`get_weather`**: Get current weather for any location
- **`get_forecast`**: Get 5-day weather forecast

**Example MCP Tool Call:**
```json
{
  "tool": "get_weather",
  "arguments": {
    "location": "New York, NY",
    "units": "metric"
  }
}
```

### LLM Client (`llm_weather_client.py`)

The client demonstrates how to:

- Connect to the local MCP server via stdio
- Call MCP tools programmatically
- Analyze weather data with a layered LLM pipeline (OpenAI / HF Inference / Ollama / rule‑based)
- Provide an interactive, looping CLI UX (implemented in `run.py`)

### Configuration (`config.py`)

Centralized configuration management with environment variable support.

## 💬 Usage Examples

### Interactive CLI

```
Enter location (e.g., 'London, UK'):
What would you like to see?
  1) Current weather
  2) 5-day forecast

Weather Assistant:
Current Weather for London, GB:
🌡️ Temperature: 15°C (feels like 13°C)
🌤️ Conditions: Partly Cloudy
💧 Humidity: 72%
💨 Wind Speed: 3.5 m/s
🔽 Pressure: 1013 hPa
👁️ Visibility: 10000 meters

🤖 Analysis: 🌤️ The temperature is moderate and comfortable.
```

### Forecast Queries

```
Enter location: Tokyo, JP
Choose: 2 (5-day forecast)

Weather Assistant:
5-Day Weather Forecast for Tokyo, JP:

📅 2024-01-15: 8°C, Clear Sky, Humidity: 45%
📅 2024-01-16: 12°C, Few Clouds, Humidity: 52%
📅 2024-01-17: 10°C, Light Rain, Humidity: 78%
📅 2024-01-18: 7°C, Overcast Clouds, Humidity: 65%
📅 2024-01-19: 9°C, Partly Cloudy, Humidity: 58%
```

## 🛠️ Advanced Usage

### Programmatic API Usage

```python
from llm_weather_client import WeatherLLMClient

async def get_weather_data():
    client = WeatherLLMClient()
    await client.connect_to_mcp_server()
    
    # Get current weather
    weather = await client.get_weather("Paris, France")
    print(weather)
    
    # Get forecast
    forecast = await client.get_forecast("Paris, France")
    print(forecast)
    
    await client.disconnect()
```

### Custom MCP Server Integration

You can run the MCP server standalone and connect to it from other MCP clients:

```bash
python weather_mcp_server.py
```

## 🔌 MCP Protocol Details

This project implements the Model Context Protocol specification:

- **Resources**: Weather data resources (`weather://current`)
- **Tools**: Weather fetching tools (`get_weather`, `get_forecast`)
- **Stdio Transport**: Communication via stdin/stdout
- **JSON-RPC**: Standard MCP message format

### Available MCP Tools

1. **get_weather**
   - Description: Get current weather information
   - Parameters: `location` (required), `units` (optional)
   - Returns: Formatted weather data

2. **get_forecast**
   - Description: Get 5-day weather forecast
   - Parameters: `location` (required), `units` (optional)
   - Returns: Formatted forecast data

## 🧪 Testing

Test the MCP server directly:

```bash
# Test server startup
python weather_mcp_server.py

# Test client connection
python llm_weather_client.py
```

## 🔒 Security Notes

- API keys are loaded from environment variables
- No API keys are hardcoded in the source code
- The `.env` file is excluded from version control

## 🚧 Extending the Project

### Add More Weather Data

Extend the MCP server to include:
- Air quality data
- Weather alerts
- Historical weather data
- Satellite imagery

### Integrate Real LLM

Replace the simple rule-based analysis with a real LLM:

```python
import openai

def analyze_weather_with_gpt(weather_data, user_query):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a weather expert assistant."},
            {"role": "user", "content": f"Weather data: {weather_data}\nUser question: {user_query}"}
        ]
    )
    return response.choices[0].message.content
```

### Add More MCP Tools

Extend the server with additional tools:
- Location search and geocoding
- Weather comparisons between cities
- Weather-based recommendations

## 📚 Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [OpenWeatherMap API Documentation](https://openweathermap.org/api)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **"OPENWEATHER_API_KEY not set"**
   - Make sure you've created a `.env` file with your API key
   - Verify the API key is valid at openweathermap.org

2. **"Location not found"**
   - Check the spelling of the location
   - Try using "City, Country" format (e.g., "London, UK")

3. **MCP Connection Issues**
   - Ensure all dependencies are installed
   - Check that the MCP server starts without errors

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export MCP_DEBUG=1
python llm_weather_client.py
```

## 🎯 Next Steps

This project demonstrates the basics of MCP integration. Consider exploring:

- Integration with other MCP servers
- Building a web interface
- Adding voice interaction capabilities
- Implementing weather-based automation
