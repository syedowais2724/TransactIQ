# AI-Powered Transaction Processing Pipeline - Frontend

A world-class premium SaaS dashboard built with Next.js 14, TypeScript, Tailwind CSS, and Shadcn UI.

## 🚀 Tech Stack

- **Next.js 14** - App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **Shadcn UI** - Premium component library
- **Framer Motion** - Smooth animations
- **Recharts** - Beautiful charts
- **Axios** - API client
- **Lucide Icons** - Modern icons

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx                 # Root layout with dark mode
│   ├── page.tsx                   # Landing page
│   ├── globals.css                # Global styles
│   ├── dashboard/
│   │   ├── layout.tsx             # Dashboard layout with sidebar
│   │   ├── page.tsx               # Main dashboard
│   │   ├── upload/page.tsx        # CSV upload page
│   │   ├── jobs/page.tsx          # Jobs history
│   │   ├── analytics/page.tsx     # Analytics page
│   │   └── results/[id]/page.tsx  # Job results page
│   └── api/
│       └── health/route.ts        # Health check endpoint
├── components/
│   ├── ui/                        # Shadcn UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   ├── progress.tsx
│   │   ├── badge.tsx
│   │   └── ...
│   ├── landing/
│   │   ├── Hero.tsx              # Hero section
│   │   ├── Features.tsx          # Features section
│   │   └── UploadZone.tsx        # Drag & drop upload
│   ├── dashboard/
│   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   ├── StatCard.tsx          # Stat cards
│   │   ├── Charts/
│   │   │   ├── CategoryPieChart.tsx
│   │   │   ├── MerchantBarChart.tsx
│   │   │   └── SpendingTrendChart.tsx
│   │   ├── ProcessingSteps.tsx   # Upload progress
│   │   ├── AISummary.tsx         # AI narrative card
│   │   ├── AnomaliesTable.tsx    # Anomalies display
│   │   └── TransactionsTable.tsx # Transactions table
│   └── shared/
│       ├── LoadingSkeleton.tsx
│       ├── EmptyState.tsx
│       └── ErrorBoundary.tsx
├── lib/
│   ├── api.ts                    # API client
│   ├── types.ts                  # TypeScript types
│   ├── utils.ts                  # Utility functions
│   └── hooks/
│       ├── usePolling.ts         # Poll job status
│       ├── useUpload.ts          # Upload logic
│       └── useJobs.ts            # Jobs management
├── public/
│   └── ...
├── tailwind.config.ts
├── next.config.js
└── package.json
```

## 🎨 Design Features

### Dark Mode First
- Beautiful dark theme inspired by Stripe/Vercel
- Glassmorphism effects
- Smooth color transitions

### Animations
- Framer Motion for page transitions
- Smooth loading states
- Interactive hover effects
- Animated progress indicators

### Responsive
- Mobile-first design
- Tablet optimized
- Desktop premium experience

### Premium UI
- Clean typography
- Consistent spacing
- Modern card designs
- Beautiful charts

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## 📱 Pages

### 1. Landing Page (`/`)
- Hero section with animated gradient
- Project explanation
- Feature highlights
- Drag & drop CSV upload
- Call-to-action buttons

### 2. Dashboard (`/dashboard`)
- Overview stats (INR/USD spend, transactions, anomalies)
- Risk level indicator
- Quick upload button
- Recent jobs list

### 3. Upload Page (`/dashboard/upload`)
- Drag & drop zone
- File validation
- Upload progress with stages:
  - Uploading
  - Cleaning Data
  - Detecting Anomalies
  - AI Classification
  - Generating Summary
- Auto-redirect to results

### 4. Results Page (`/dashboard/results/[id]`)
- Summary cards
- AI narrative (highlighted)
- Risk level badge
- Category pie chart
- Merchant bar chart
- Spending trend line chart
- Anomalies table (red highlighted)
- Full transactions table (searchable, sortable, paginated)
- Export options

### 5. Jobs History (`/dashboard/jobs`)
- All uploaded jobs
- Status indicators
- Timestamps
- Row counts
- Quick actions
- Filtering by status

### 6. Analytics (`/dashboard/analytics`)
- Aggregate stats across all jobs
- Trends over time
- Category insights
- Merchant analysis

## 🎯 Key Features

### CSV Upload Flow
1. User selects/drops CSV file
2. Client validates file (size, format)
3. Upload to backend with progress
4. Show animated processing stages
5. Poll status every 3 seconds
6. Auto-navigate to results when complete

### Real-time Updates
- Polling mechanism for job status
- Live progress indicators
- Animated state transitions

### Data Visualization
- **Pie Chart**: Category-wise spending breakdown
- **Bar Chart**: Top merchants by transaction amount
- **Line Chart**: Daily/weekly spending trends

### Tables
- **Anomalies Table**: Red-highlighted suspicious transactions
- **Transactions Table**:
  - Search by merchant/txn_id
  - Sort by any column
  - Pagination (10/25/50 per page)
  - Export to CSV

### AI Summary Display
- Beautiful card with gradient border
- AI-generated narrative
- Risk level with color coding
- Key insights highlighted

## 🎨 Component Examples

### Stat Card
```tsx
<StatCard
  title="Total Spend (INR)"
  value="₹75,000.00"
  icon={<IndianRupee />}
  trend={+12.5}
/>
```

### Processing Steps
```tsx
<ProcessingSteps
  currentStep="classifying"
  steps={[
    'uploading',
    'cleaning',
    'detecting',
    'classifying',
    'summarizing'
  ]}
/>
```

### AI Summary
```tsx
<AISummary
  narrative="Analysis shows concentrated spending..."
  riskLevel="medium"
  anomalyCount={3}
/>
```

## 🚀 Performance

- Static generation where possible
- Dynamic imports for charts
- Optimized images
- Code splitting
- Lazy loading

## 🔒 Error Handling

- API error boundaries
- Graceful degradation
- User-friendly error messages
- Retry mechanisms
- Fallback states

## 📦 Build for Production

```bash
npm run build
npm start
```

## 🎭 Animations

### Page Transitions
- Fade in on mount
- Slide animations
- Staggered children

### Loading States
- Skeleton screens
- Shimmer effects
- Pulse animations

### Interactive Elements
- Hover scale
- Click feedback
- Smooth transitions

## 🌈 Color Scheme

### Dark Mode (Primary)
- Background: `hsl(240 10% 3.9%)`
- Card: `hsl(240 10% 5%)`
- Primary: `hsl(0 0% 98%)`
- Accent: Gradient blues/purples

### Status Colors
- Success: Green (`#10b981`)
- Warning: Yellow (`#f59e0b`)
- Error: Red (`#ef4444`)
- Info: Blue (`#3b82f6`)

## 📝 TypeScript Types

All API responses are fully typed:
- `Job`
- `Transaction`
- `JobResults`
- `JobSummary`
- `CategoryBreakdown`

## 🎨 Tailwind Classes

Custom utilities:
- `.glass` - Glassmorphism effect
- `.shimmer` - Loading animation
- `.animated-gradient` - Moving gradient

## 🔧 Custom Hooks

- `usePolling` - Poll API endpoints
- `useUpload` - Handle file uploads
- `useJobs` - Manage jobs state
- `useDebounce` - Debounce searches

## 📱 Responsive Breakpoints

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

## 🎯 Next Steps

1. Install dependencies: `npm install`
2. Start backend: API should be running on port 8000
3. Start frontend: `npm run dev`
4. Open http://localhost:3000
5. Upload sample CSV
6. Explore the dashboard!

## 🤝 Contributing

This is a production-grade template. Customize:
- Color scheme in `globals.css`
- Components in `components/`
- Pages in `app/`
- API client in `lib/api.ts`

## 📄 License

MIT License

---

**Built with ❤️ using Next.js 14 and modern web technologies**
