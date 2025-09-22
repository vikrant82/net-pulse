# Net-Pulse Frontend

A modern network monitoring dashboard built with SvelteKit, featuring real-time traffic visualization and a professional dark blue/teal theme.

## 🚀 Features

- **Real-time Network Monitoring**: Live traffic data visualization
- **Modern UI**: Built with Shadcn/ui components and Tailwind CSS
- **Dark/Light Theme**: Automatic theme switching with smooth transitions
- **Responsive Design**: Mobile-first approach with accessibility compliance
- **TypeScript Support**: Full type safety throughout the application
- **Chart.js Integration**: Interactive data visualization
- **Professional Styling**: Custom Net-Pulse color palette

## 🛠️ Tech Stack

- **Framework**: SvelteKit
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui
- **Charts**: Chart.js with date-fns adapter
- **Icons**: Lucide Svelte
- **HTTP Client**: Axios

## 📦 Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── app.html              # Main HTML template
│   ├── app.css               # Global styles and theme variables
│   ├── lib/
│   │   ├── components/       # Reusable UI components
│   │   ├── stores/          # Svelte stores for state management
│   │   ├── types/           # TypeScript type definitions
│   │   └── utils/           # Utility functions
│   └── routes/              # SvelteKit routes
├── static/                  # Static assets
└── package.json            # Dependencies and scripts
```

## 🎨 Theme Configuration

The application uses a custom dark blue/teal color palette:

- **Primary Colors**: Blue shades (#0ea5e9, #0284c7, #0369a1)
- **Accent Colors**: Teal shades (#14b8a6, #0d9488, #0f766e)
- **Status Colors**: Success (#10b981), Warning (#f59e0b), Error (#ef4444)

## 🔧 API Integration

The frontend is designed to work with the Net-Pulse backend API:

- **Base URL**: `http://localhost:8000`
- **Key Endpoints**:
  - `/api/interfaces` - Network interface information
  - `/api/traffic/history` - Historical traffic data
  - `/api/traffic/latest` - Latest traffic statistics
  - `/api/system/info` - System information

## 📱 Responsive Design

- **Mobile**: < 768px - Bottom navigation, stacked layout
- **Tablet**: 768px - 1024px - Side navigation, condensed layout
- **Desktop**: > 1024px - Full navigation, optimal spacing

## ♿ Accessibility

- **WCAG 2.1 AA Compliance**: Full accessibility support
- **Keyboard Navigation**: Complete keyboard support
- **Screen Reader Support**: Semantic HTML and ARIA labels
- **High Contrast Mode**: Support for high contrast displays

## 🚀 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Run TypeScript checks
- `npm run lint` - Run ESLint and Prettier

### Environment Variables

Create a `.env` file in the root directory:

```env
PUBLIC_API_BASE_URL=http://localhost:8000
PUBLIC_APP_NAME=Net-Pulse
PUBLIC_APP_VERSION=1.0.0
```

## 📄 License

This project is part of the Net-Pulse network monitoring system.