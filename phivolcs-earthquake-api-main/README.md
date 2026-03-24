# PHIVOLCS Earthquake Data API

A Node.js Express server that fetches and parses earthquake data from PHIVOLCS (Philippine Institute of Volcanology and Seismology).

## 🚀 Quick Start

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation

1. **Create a new directory and navigate to it:**
```bash
mkdir phivolcs-api
cd phivolcs-api
```

2. **Save the files:**
   - Save `server.js` (the Express server code)
   - Save `package.json` (the dependencies file)

3. **Install dependencies:**
```bash
npm install
```

4. **Start the server:**
```bash
npm start
```

Or for development with auto-reload:
```bash
npm run dev
```

The server will start on `http://localhost:3001`

## 📡 API Endpoints

### Get Earthquake Data
```
GET http://localhost:3001/api/earthquakes
```

Returns cached earthquake data (cached for 5 minutes).

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "dateTime": "2024-10-01 10:30:00 AM",
      "latitude": "14.58",
      "longitude": "121.05",
      "depth": "10 km",
      "magnitude": "3.2",
      "location": "5 km S 45° W of Manila"
    }
  ],
  "cached": false,
  "lastUpdated": "2024-10-01T02:30:00.000Z",
  "count": 150
}
```

### Force Refresh
```
GET http://localhost:3001/api/earthquakes/refresh
```

Forces a fresh fetch from PHIVOLCS, ignoring cache.

### Health Check
```
GET http://localhost:3001/health
```

Returns server status and cache information.

## 🔧 Features

- ✅ Bypasses SSL certificate issues
- ✅ Caching system (5-minute cache to reduce load)
- ✅ CORS enabled for frontend access
- ✅ Error handling and detailed logging
- ✅ Parses HTML table from PHIVOLCS website
- ✅ Returns clean JSON data

## 💻 Using with Frontend

Update your React component to use this backend:

```javascript
const fetchData = async () => {
  setLoading(true);
  setError(null);
  
  try {
    const response = await fetch('http://localhost:3001/api/earthquakes');
    const result = await response.json();
    
    if (result.success) {
      setEarthquakes(result.data);
      setLastUpdated(new Date(result.lastUpdated));
    } else {
      setError(result.error);
    }
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Change PORT in server.js or set environment variable
PORT=3002 npm start
```

**SSL Certificate errors:**
The server is configured to ignore SSL certificate errors from PHIVOLCS. This is handled in the code with `rejectUnauthorized: false`.

**No data returned:**
- Check if PHIVOLCS website is accessible
- Check server console logs for detailed error messages
- Try the `/api/earthquakes/refresh` endpoint

## 📝 Notes

- Data is cached for 5 minutes to reduce load on PHIVOLCS servers
- The server runs on port 3001 by default
- SSL certificate verification is disabled for PHIVOLCS domain
- CORS is enabled for all origins (adjust in production)

## 🔒 Production Considerations

For production deployment:
1. Enable SSL certificate verification (remove `rejectUnauthorized: false`)
2. Restrict CORS to specific domains
3. Add rate limiting
4. Add authentication if needed
5. Use environment variables for configuration
6. Add proper logging system
7. Consider using a process manager like PM2