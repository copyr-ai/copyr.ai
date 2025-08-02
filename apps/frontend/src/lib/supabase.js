import { createBrowserClient } from '@supabase/ssr'

let supabase = null

export function getSupabaseClient() {
  if (!supabase) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    
    // Check if environment variables are properly configured
    if (!supabaseUrl || !supabaseAnonKey || 
        supabaseUrl === 'your_supabase_url_here' || 
        supabaseAnonKey === 'your_supabase_anon_key_here') {
      console.warn('Supabase environment variables not configured. Authentication will not work.')
      // Return a mock client that won't cause errors
      return {
        auth: {
          getSession: () => Promise.resolve({ data: { session: null } }),
          signInWithOAuth: () => Promise.resolve({ data: null, error: { message: 'Supabase not configured' } }),
          signOut: () => Promise.resolve({ error: null }),
          onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } })
        },
        from: () => ({
          select: () => ({ eq: () => ({ single: () => Promise.resolve({ data: null, error: null }) }) }),
          insert: () => ({ select: () => ({ single: () => Promise.resolve({ data: null, error: null }) }) }),
          update: () => ({ eq: () => ({ select: () => ({ single: () => Promise.resolve({ data: null, error: null }) }) }) }),
          delete: () => ({ eq: () => Promise.resolve({ data: null, error: null }) })
        })
      }
    }
    
    supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)
  }
  return supabase
}

// Export for direct use
export const supabaseClient = getSupabaseClient()