'use client'

import { createContext, useContext, useState, useEffect } from 'react'
import { supabaseClient } from '../lib/supabase'
import { apiClient } from '../lib/api'

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
    // Use environment variables for redirect URL
    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.NEXT_PUBLIC_APP_URL || window.location.origin;
    
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${siteUrl}/auth/callback`
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

  // Get user profile from backend API
  const getUserProfile = async (userId) => {
    if (!userId) return null
    
    try {
      const profile = await apiClient.getUserProfile(userId)
      return profile
    } catch (error) {
      console.error('Error fetching user profile:', error)
      return null
    }
  }

  // Update user profile (TODO: Implement backend endpoint)
  const updateProfile = async (profileData) => {
    if (!user) return { error: 'No user logged in' }
    
    // TODO: Use backend API when endpoint is available
    console.warn('Profile update not implemented yet - backend endpoint needed')
    return { error: 'Profile update not implemented' }
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
          // Get profile from backend - it will be created automatically if it doesn't exist
          const userProfile = await getUserProfile(session.user.id)
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
            // Get profile from backend - it will be created automatically if it doesn't exist
            const userProfile = await getUserProfile(session.user.id)
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