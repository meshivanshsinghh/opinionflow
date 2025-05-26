# OpinionFlow - AI Product Review Intelligence

A modern React application that provides AI-powered cross-store product review intelligence. Compare products across Amazon and Walmart with intelligent review analysis.

## Features

- 🔍 **Product Discovery**: Search for products across multiple stores (Amazon, Walmart)
- 📊 **Review Analysis**: AI-powered sentiment analysis and review processing
- 💬 **Interactive Chat**: Ask questions about products and get intelligent responses
- 📈 **Comprehensive Reports**: Detailed analysis including pros/cons, themes, and recommendations
- 🎨 **Modern UI**: Beautiful, responsive design with Tailwind CSS
- ⚡ **Fast Performance**: Built with Next.js for optimal performance

## Tech Stack

- **Frontend**: Next.js 15, React 18
- **Styling**: Tailwind CSS 4
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Markdown**: React Markdown
- **Utilities**: UUID, clsx

## Prerequisites

- Node.js 18+
- npm or yarn
- Backend API server running (see backend setup instructions)

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd react-frontend
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Environment Configuration**
   Create a `.env.local` file in the root directory:

   ```env
   NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1
   ```

4. **Start the development server**

   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Usage

### 1. Product Discovery

- Enter a product name in the search box (e.g., "iPhone 14 Pro", "Nike Air Max")
- Click "Discover Products" to search across stores
- View products from Amazon and Walmart with images, prices, and ratings

### 2. Product Selection

- Click on products to select them for comparison
- You can select one product from each store
- Selected products will be highlighted in green
- Click "Analyze Reviews" when ready

### 3. Review Analysis

- The system will extract and analyze reviews from selected products
- View comprehensive analysis including:
  - Executive summary
  - Sentiment analysis with ratings breakdown
  - Pros and cons comparison
  - Common discussion themes
  - Product comparisons (if multiple products selected)
  - Key insights and recommendations

### 4. Interactive Chat

- Ask questions about your selected products
- Get AI-powered responses based on review analysis
- Use suggested questions or ask your own
- View sources and confidence levels for responses

## API Integration

The application connects to a backend API with the following endpoints:

- `POST /products/discover` - Search for products
- `POST /reviews/extract` - Extract reviews from selected products
- `POST /analysis/analyze` - Analyze extracted reviews
- `POST /analysis/question` - Ask questions about analyzed products

## Project Structure

```
src/
├── app/
│   ├── globals.css          # Global styles
│   ├── layout.js           # Root layout component
│   └── page.js             # Main page component
├── components/
│   ├── OpinionFlow.js      # Main application component
│   ├── ProductSearch.js    # Product search interface
│   ├── ProductSelection.js # Product selection and display
│   ├── AnalysisResults.js  # Analysis results display
│   └── ChatInterface.js    # Interactive chat component
└── utils/
    └── api.js              # API configuration and helpers
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Customization

### Styling

The application uses Tailwind CSS for styling. You can customize:

- Colors and themes in `tailwind.config.js`
- Global styles in `src/app/globals.css`
- Component-specific styles in individual component files

### API Configuration

Update the API base URL in:

- `.env.local` for environment-specific configuration
- `src/utils/api.js` for default configuration

### Features

Add new features by:

- Creating new components in `src/components/`
- Adding new API endpoints in `src/utils/api.js`
- Extending the main `OpinionFlow.js` component

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy automatically

### Other Platforms

1. Build the application: `npm run build`
2. Deploy the `out` directory to your hosting platform
3. Ensure environment variables are configured

## Troubleshooting

### Common Issues

1. **API Connection Errors**

   - Ensure backend server is running
   - Check API_BASE URL in environment variables
   - Verify CORS settings on backend

2. **Build Errors**

   - Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
   - Check for TypeScript errors if using TypeScript

3. **Styling Issues**
   - Ensure Tailwind CSS is properly configured
   - Check for conflicting CSS classes

### Performance Optimization

- Images are optimized automatically by Next.js
- API calls include timeout configurations
- Components use React best practices for re-rendering

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the GitHub repository
- Check the documentation
- Review the troubleshooting section

---

Built with ❤️ using Next.js and React
