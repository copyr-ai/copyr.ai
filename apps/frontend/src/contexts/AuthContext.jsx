'use client'

import { createContext, useContext, useState, useEffect } from 'react'
import { supabaseClient } from '@/lib/supabase'
import { apiClient } from '@/lib/api'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  // Sign in with Google
  const signInWithGoogle = async () => {
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
    
    if (error && error.message === 'Supabase not configured') {
      alert('Authentication is not configured yet. Please set up your Supabase environment variables.')
    }
    
    return { data, error }
  }

  // Sign out
  const signOut = async () => {
    const { error } = await supabaseClient.auth.signOut()
    if (!error) {
      setUser(null)
      setProfile(null)
    }
    return { error }
  }

  // Create user profile if it doesn't exist
  const createUserProfile = async (user) => {
    if (!user) return null
    
    const { data, error } = await supabaseClient
      .from('user_profiles')
      .insert({
        id: user.id,
        email: user.email,
        full_name: user.user_metadata?.full_name || user.user_metadata?.name,
        avatar_url: user.user_metadata?.avatar_url || user.user_metadata?.picture
      })
      .select()
      .single()
    
    if (error) {
      console.error('Error creating user profile:', error)
      return null
    }
    
    return data
  }

  // Get user profile
  const getUserProfile = async (userId) => {
    if (!userId) return null
    
    const { data, error } = await supabaseClient
      .from('user_profiles')
      .select('*')
      .eq('id', userId)
      .maybeSingle() // Use maybeSingle() instead of single() to handle 0 rows gracefully
    
    if (error) {
      console.error('Error fetching user profile:', error)
      return null
    }
    
    return data
  }

  // Update user profile
  const updateProfile = async (profileData) => {
    if (!user) return { error: 'No user logged in' }
    
    const { data, error } = await supabaseClient
      .from('user_profiles')
      .update(profileData)
      .eq('id', user.id)
      .select()
      .single()
    
    if (!error && data) {
      setProfile(data)
    }
    
    return { data, error }
  }

  // Save search to history
  const saveSearchToHistory = async (searchData) => {
    if (!user) return { error: 'No user logged in' }
    
    try {
      const data = await apiClient.saveSearchHistory(user.id, {
        query_text: searchData.query,
        filters: searchData.filters || {},
        results: searchData.results || [],
        result_count: searchData.results?.length || 0
      })
      return { data, error: null }
    } catch (error) {
      return { data: null, error: error.message }
    }
  }

  // Get user search history
  const getSearchHistory = async (limit = 20) => {
    if (!user) return { data: [], error: 'No user logged in' }
    
    try {
      const data = await apiClient.getUserSearchHistory(user.id, limit)
      return { data: data || [], error: null }
    } catch (error) {
      return { data: [], error: error.message }
    }
  }

  // Delete search history item
  const deleteSearchHistory = async (historyId) => {
    if (!user) return { error: 'No user logged in' }
    
    try {
      const data = await apiClient.deleteSearchHistoryItem(user.id, historyId)
      return { data, error: null }
    } catch (error) {
      return { data: null, error: error.message }
    }
  }

  useEffect(() => {
    let mounted = true

    // Get initial session
    const getInitialSession = async () => {
      const { data: { session } } = await supabaseClient.auth.getSession()
      
      if (mounted) {
        if (session?.user) {
          setUser(session.user)
          let userProfile = await getUserProfile(session.user.id)
          
          // If profile doesn't exist, create it
          if (!userProfile) {
            userProfile = await createUserProfile(session.user)
          }
          
          setProfile(userProfile)
        }
        setLoading(false)
      }
    }

    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabaseClient.auth.onAuthStateChange(
      async (event, session) => {
        if (mounted) {
          if (session?.user) {
            setUser(session.user)
            let userProfile = await getUserProfile(session.user.id)
            
            // If profile doesn't exist, create it
            if (!userProfile) {
              userProfile = await createUserProfile(session.user)
            }
            
            setProfile(userProfile)
          } else {
            setUser(null)
            setProfile(null)
          }
          setLoading(false)
        }
      }
    )

    return () => {
      mounted = false
      subscription?.unsubscribe()
    }
  }, [])

  const value = {
    user,
    profile,
    loading,
    signInWithGoogle,
    signOut,
    updateProfile,
    saveSearchToHistory,
    getSearchHistory,
    deleteSearchHistory
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}