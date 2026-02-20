# KrishiMitra AI - Setup Instructions

## Prerequisites
- Node.js (v16 or higher)
- npm, yarn, or bun package manager

## Installation Steps

### 1. Install Dependencies
Open your terminal in VS Code and run one of the following commands:

```bash
# Using npm
npm install

# Using yarn
yarn install

# Using bun (fastest)
bun install
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory with your backend API URL:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_NOMINATIM_URL=https://nominatim.openstreetmap.org
```

### 3. Start Development Server
Run one of the following commands:

```bash
# Using npm
npm run dev

# Using yarn
yarn dev

# Using bun
bun dev
```

The application will start at `http://localhost:5173` (or another port if 5173 is busy).

### 4. Access the Application
1. Open your browser and navigate to `http://localhost:5173`
2. You'll see the onboarding screen with language selection
3. Complete the 3-step setup process:
   - Step 1: Personal Information (Name, Age, Mobile, Farm Location)
   - Step 2: Farm Information (Crops, Experience, Soil Type)
   - Step 3: Complete Setup
4. After setup, you'll be redirected to the Home screen

## Features
- **Caching**: All API responses are cached for 30 minutes to improve performance
- **Offline Support**: The app works with local storage when offline
- **Multi-language**: Supports 10+ Indian languages
- **GPS Integration**: Auto-detect farm location using GPS

## Build for Production

```bash
# Using npm
npm run build

# Using yarn
yarn build

# Using bun
bun run build
```

The production build will be in the `dist` folder.

## Troubleshooting

### Port Already in Use
If port 5173 is busy, Vite will automatically use the next available port. Check the terminal output for the actual URL.

### API Connection Issues
- Ensure your backend server is running at the URL specified in `.env`
- Check that CORS is properly configured on your backend
- Verify the API endpoints are accessible

### Dependencies Issues
Try clearing the cache and reinstalling:

```bash
rm -rf node_modules package-lock.json
npm install
```

## Project Structure
```
src/
├── pages/          # Main application pages
├── components/     # Reusable UI components
├── lib/            # API client and utilities
└── assets/         # Images and static files
```

## Development Tips
- Hot reload is enabled - changes will reflect immediately
- Use browser DevTools to inspect network requests
- Check the console for any errors or warnings
- All data is cached locally - clear localStorage to reset

## Contact
For issues or questions, please refer to the project documentation.
