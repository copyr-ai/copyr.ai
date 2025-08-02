# Authentication Setup Guide

This guide walks you through setting up authentication for the copyr.ai application.

## Phase 1: Database Setup

### 1. Run SQL Schema in Supabase

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `apps/backend/sql/create_tables.sql`
4. Execute the SQL to create the authentication tables

### 2. Configure Environment Variables

#### Backend (.env file in apps/backend/)
```bash
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

#### Frontend (.env.local file in apps/frontend/)
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Phase 2: Google OAuth Configuration

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Google+ API" and "People API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized redirect URIs:
   - `https://your-supabase-project.supabase.co/auth/v1/callback`
   - `http://localhost:3000/auth/callback` (for development)

### 2. Supabase OAuth Configuration

1. In your Supabase dashboard, go to Authentication → Providers
2. Enable Google provider
3. Add your Google OAuth credentials:
   - Client ID from Google Cloud Console
   - Client Secret from Google Cloud Console
4. Set redirect URL to: `http://localhost:3000/auth/callback`

## Phase 3: Testing Authentication

### 1. Start the Applications

```bash
# Terminal 1 - Backend
cd apps/backend
python main.py

# Terminal 2 - Frontend  
cd apps/frontend
npm run dev
```

### 2. Test the Authentication Flow

1. Open http://localhost:3000
2. Click "Sign in with Google" in the navbar
3. Complete Google OAuth flow
4. Verify user profile appears in navbar
5. Check user_profiles table in Supabase for new user record

## Phase 4: Search History Integration

Once authentication is working, searches will automatically be saved to user history when:
- User is logged in
- User performs a search
- Search results are returned

You can view search history by:
1. Logging in
2. Clicking on profile avatar in navbar
3. Clicking "View Search History"

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Check Google Cloud Console redirect URIs match Supabase settings
   - Ensure no trailing slashes in URLs

2. **"User not found in database"**
   - Check if the `handle_new_user()` trigger is working
   - Manually verify trigger exists in Supabase SQL Editor

3. **CORS errors**
   - Backend allows localhost:3000 by default
   - Check CORS settings in `apps/backend/main.py`

4. **Environment variables not loading**
   - Restart development servers after adding .env files
   - Check file names (.env vs .env.local)

### Development vs Production

For production deployment:
1. Update redirect URIs in Google Cloud Console
2. Update NEXT_PUBLIC_API_URL to production backend URL
3. Configure production environment variables
4. Update CORS settings in backend for production domain