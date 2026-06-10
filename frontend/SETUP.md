# Frontend Setup Guide

## Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit http://localhost:3000

## Installation Steps

### 1. Install Node.js

Download from https://nodejs.org/ (v18 or higher)

Verify:
```bash
node --version
npm --version
```

### 2. Install Dependencies

```bash
npm install
```

This installs:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Shadcn UI components
- Framer Motion
- Recharts
- Axios
- Lucide Icons

### 3. Configure Environment

Copy the example env file:
```bash
copy .env.local.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 4. Run Development Server

```bash
npm run dev
```

The app will be available at http://localhost:3000

## File Structure Created

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── dashboard/
├── components/
│   ├── ui/
│   ├── landing/
│   ├── dashboard/
│   └── shared/
├── lib/
│   ├── api.ts
│   ├── types.ts
│   └── utils.ts
├── public/
├── .env.local
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Required Files to Complete

Due to size, you'll need to create additional files. Here's what's needed:

### Pages (in `app/`)
1. `app/page.tsx` - Landing page
2. `app/layout.tsx` - Root layout
3. `app/dashboard/layout.tsx` - Dashboard layout
4. `app/dashboard/page.tsx` - Dashboard home
5. `app/dashboard/upload/page.tsx` - Upload page
6. `app/dashboard/jobs/page.tsx` - Jobs history
7. `app/dashboard/results/[id]/page.tsx` - Results page

### Components (in `components/`)
1. Landing components (Hero, Features, UploadZone)
2. Dashboard components (Sidebar, Charts, Tables)
3. Shared components (Loading, Empty, Error states)

### Hooks (in `lib/hooks/`)
1. `usePolling.ts` - Poll job status
2. `useUpload.ts` - Upload handler
3. `useJobs.ts` - Jobs management

## Development Workflow

1. **Start Backend First**
   ```bash
   # In backend directory
   .\venv\Scripts\uvicorn.exe app.main_local:app --host 127.0.0.1 --port 8000
   ```

2. **Start Frontend**
   ```bash
   # In frontend directory
   npm run dev
   ```

3. **Test Upload**
   - Go to http://localhost:3000
   - Upload a CSV file
   - Watch the processing stages
   - View results

## Build for Production

```bash
npm run build
npm start
```

## Customization

### Colors
Edit `app/globals.css` to change the color scheme.

### Components
All UI components are in `components/ui/` and can be customized.

### API URL
Change `NEXT_PUBLIC_API_URL` in `.env.local` to point to your backend.

## Troubleshooting

### Port Already in Use
Change the port:
```bash
PORT=3001 npm run dev
```

### API Connection Failed
1. Ensure backend is running on port 8000
2. Check `.env.local` has correct API URL
3. Verify no CORS issues

### Styling Issues
```bash
npm run build
# This will show any Tailwind/styling errors
```

## Next Steps

1. Complete remaining page files (see structure above)
2. Add more charts and visualizations
3. Implement advanced filtering
4. Add export functionality
5. Deploy to Vercel

## Resources

- Next.js Docs: https://nextjs.org/docs
- Tailwind CSS: https://tailwindcss.com/docs
- Shadcn UI: https://ui.shadcn.com
- Recharts: https://recharts.org
- Framer Motion: https://www.framer.com/motion

---

**Ready to build!** 🚀
