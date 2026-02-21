#!/usr/bin/env python3
"""
Weather and News Agent for Multi-Agent Project
Fetches weather and local news for a given city/zip and sends email report
"""
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Import our storage system
from store_weather_news import WeatherNewsStorage

# Load environment variables
load_dotenv()

class WeatherNewsAgent:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
        self.username = os.getenv('EMAIL_USERNAME')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.from_email = os.getenv('EMAIL_FROM')
        self.to_email = os.getenv('EMAIL_TO', self.username)  # Default to same as username
        
        # API Keys from environment variables
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.news_api_key = os.getenv('NEWS_API_KEY')
        
    def get_location_input(self):
        """Get city or zip code from user"""
        location = input("🏙️  Enter city name or zip code: ").strip()
        if not location:
            print(" Please enter a valid city or zip code")
            return self.get_location_input()
        return location
    
    def get_weather_data(self, location):
        """Fetch weather data from OpenWeatherMap API"""
        try:
            # First get coordinates
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={self.weather_api_key}"
            geo_response = requests.get(geo_url)
            geo_data = geo_response.json()
            
            if not geo_data:
                return f" Could not find location: {location}"
            
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            city_name = geo_data[0]['name']
            
            # Get weather data
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.weather_api_key}&units=metric"
            weather_response = requests.get(weather_url)
            weather_data = weather_response.json()
            
            if weather_data.get('cod') != 200:
                return f" Error fetching weather data: {weather_data.get('message', 'Unknown error')}"
            
            # Format weather information
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            description = weather_data['weather'][0]['description'].title()
            wind_speed = weather_data['wind']['speed']
            
            weather_info = f"""
📍 Location: {city_name}
🌡️  Temperature: {temp}°C (feels like {feels_like}°C)
☁️  Conditions: {description}
💧 Humidity: {humidity}%
💨 Wind Speed: {wind_speed} m/s
"""
            return weather_info
            
        except Exception as e:
            return f" Error fetching weather: {str(e)}"
    
    def get_local_news(self, location):
        """Fetch local news using NewsAPI"""
        try:
            # Try to get country code for location
            country = self.get_country_code(location)
            
            # Get top headlines for the country
            news_url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={self.news_api_key}"
            news_response = requests.get(news_url)
            news_data = news_response.json()
            
            if news_data.get('status') != 'ok':
                return f" Error fetching news: {news_data.get('message', 'Unknown error')}"
            
            articles = news_data.get('articles', [])
            
            if not articles:
                return " No news available for this location"
            
            # Format news
            news_info = "\nTOP HEADLINES:\n"
            for i, article in enumerate(articles[:5], 1):  # Get top 5 articles
                title = article['title']
                source = article['source']['name']
                news_info += f"\n{i}. {title}\n   Source: {source}\n"
            
            return news_info
            
        except Exception as e:
            return f"Error fetching news: {str(e)}"
    
    def get_country_code(self, location):
        """Get country code for location (simplified)"""
        # This is a simplified version - in a real app, you'd use a geocoding service
        location_lower = location.lower()
        
        # Common country mappings
        if any(city in location_lower for city in ['new york', 'los angeles', 'chicago', 'houston', 'phoenix']):
            return 'us'
        elif any(city in location_lower for city in ['london', 'manchester', 'birmingham', 'glasgow']):
            return 'gb'
        elif any(city in location_lower for city in ['toronto', 'vancouver', 'montreal', 'calgary']):
            return 'ca'
        elif any(city in location_lower for city in ['sydney', 'melbourne', 'brisbane', 'perth']):
            return 'au'
        elif any(city in location_lower for city in ['berlin', 'munich', 'hamburg', 'frankfurt']):
            return 'de'
        elif any(city in location_lower for city in ['paris', 'marseille', 'lyon', 'toulouse']):
            return 'fr'
        elif any(city in location_lower for city in ['madrid', 'barcelona', 'valencia', 'seville']):
            return 'es'
        elif any(city in location_lower for city in ['moscow', 'saint petersburg', 'novosibirsk']):
            return 'ru'
        elif any(city in location_lower for city in ['beijing', 'shanghai', 'guangzhou', 'shenzhen']):
            return 'cn'
        elif any(city in location_lower for city in ['mumbai', 'delhi', 'bangalore', 'hyderabad']):
            return 'in'
        else:
            # Default to US for unknown locations
            return 'us'
    
    def create_email_content(self, location, weather_info, news_info):
        """Create HTML email content"""
        html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .content {{ background-color: #f8f9fa; padding: 25px; border-radius: 10px; margin-top: 20px; }}
        .weather-box {{ background-color: #e3f2fd; padding: 20px; border-left: 4px solid #2196f3; margin: 20px 0; border-radius: 5px; }}
        .news-box {{ background-color: #fff3e0; padding: 20px; border-left: 4px solid #ff9800; margin: 20px 0; border-radius: 5px; }}
        .footer {{ background-color: #f1f3f4; padding: 15px; border-radius: 5px; margin-top: 20px; font-size: 12px; color: #666; }}
        h1 {{ margin: 0; font-size: 28px; }}
        h2 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .timestamp {{ font-size: 14px; color: #666; margin-top: 10px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
        .highlight {{ background-color: #fff; padding: 15px; border-radius: 5px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Weather & News Report</h1>
        <p style="margin: 10px 0 0 0; font-size: 18px;">Your daily update for {location}</p>
        <div class="timestamp"> Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
    </div>
    
    <div class="content">
        <div class="weather-box">
            <h2>Weather Information</h2>
            <div class="highlight">
                {weather_info}
            </div>
        </div>
        
        <div class="news-box">
            <h2>📰 Local & National News</h2>
            <div class="highlight">
                {news_info}
            </div>
        </div>
        
        <div class="footer">
            <p><strong>🤖 Multi-Agent System</strong></p>
            <p>This report was automatically generated by your multi-agent weather and news system.</p>
            <p>For more detailed information, visit your local weather service and news websites.</p>
        </div>
    </div>
</body>
</html>
"""
        
        text_content = f"""
WEATHER & NEWS REPORT
=====================

Location: {location}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

WEATHER INFORMATION:
{weather_info}

LOCAL & NATIONAL NEWS:
{news_info}

---
This report was automatically generated by your multi-agent weather and news system.
"""
        
        return html_content, text_content
    
    def send_report_email(self, location, weather_info, news_info):
        """Send the weather and news report via email"""
        try:
            # Create email content
            html_content, text_content = self.create_email_content(location, weather_info, news_info)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = f"🌤️ Daily Weather & News Report - {location}"
            message['From'] = self.from_email
            message['To'] = self.to_email
            
            # Add content
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.from_email, self.to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f" Error sending email: {e}")
            return False
    
    def run(self):
        """Main execution method"""
        print(" Weather & News Agent")
        print("=" * 50)
        
        # Get location input
        location = self.get_location_input()
        print(f" Fetching data for: {location}")
        
        # Fetch weather data
        print("  Fetching weather data...")
        weather_info = self.get_weather_data(location)
        
        # Fetch news data
        print(" Fetching local news...")
        news_info = self.get_local_news(location)
        
        # Display results
        print("\n" + "=" * 50)
        print("WEATHER & NEWS SUMMARY")
        print("=" * 50)
        print(f"Location: {location}")
        print("\n WEATHER:")
        print(weather_info)
        print("\n NEWS:")
        print(news_info)
        
        # Send email report
        print("\nSending email report...")
        if self.send_report_email(location, weather_info, news_info):
            print("✅ Email report sent successfully!")
            print(f"📧 Sent to: {self.to_email}")
        else:
            print(" Failed to send email report")
        
        print("\n Thanks!")

def main():
    """Main function"""
    print(" Starting Weather & News Agent...")
    
    # Check if API keys are set
    agent = WeatherNewsAgent()
    
    if agent.weather_api_key == "YOUR_OPENWEATHER_API_KEY":
        print(" Warning: You need to set up API keys!")
        print("1. Get a free API key from: https://openweathermap.org/api")
        print("2. Get a free API key from: https://newsapi.org/")
        print("3. Update the weather_api_key and news_api_key in the script")
        print("\nFor now, using mock data...")
        
        # Use mock data for demonstration
        mock_weather = """
📍 Location: Demo City
🌡️  Temperature: 22°C (feels like 24°C)
☁️  Conditions: Partly Cloudy
💧 Humidity: 65%
💨 Wind Speed: 5.2 m/s
"""
        mock_news = """
📰 TOP HEADLINES:

1. Breaking: Major weather update for your area
   Source: National Weather Service

2. Local sports team wins championship
   Source: Sports Network

3. National economy shows growth
   Source: Financial Times

4. Technology sector announces new developments
   Source: Tech Daily

5. Health updates and community news
   Source: Local News
"""
        
        location = agent.get_location_input()
        if agent.send_report_email(location, mock_weather, mock_news):
            print("Mock email report sent successfully!")
        else:
            print(" Failed to send mock email report")
    else:
        # Run with real API keys
        agent.run()

if __name__ == "__main__":
    main()