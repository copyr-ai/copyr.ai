'use client'

import { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './AuthContext'

const SearchLimitContext = createContext({})

export const useSearchLimit = () => {
  const context = useContext(SearchLimitContext)
  if (!context) {
    throw new Error('useSearchLimit must be used within SearchLimitProvider')
  }
  return context
}

export const SearchLimitProvider = ({ children }) => {
  const { user } = useAuth()
  const [searchCount, setSearchCount] = useState(0)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [isLimitReached, setIsLimitReached] = useState(false)
  
  const SEARCH_LIMIT = 2
  const STORAGE_KEY = 'copyr_search_count'

  // Load search count from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedCount = localStorage.getItem(STORAGE_KEY)
      if (storedCount) {
        const count = parseInt(storedCount, 10)
        setSearchCount(count)
        setIsLimitReached(count >= SEARCH_LIMIT)
      }
    }
  }, [])

  // Reset search count when user logs in
  useEffect(() => {
    if (user) {
      setSearchCount(0)
      setIsLimitReached(false)
      setShowLoginModal(false)
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY)
      }
    }
  }, [user])

  // Check if user can perform a search (allow up to SEARCH_LIMIT searches)
  const canSearch = () => {
    if (user) return true // Logged in users have unlimited searches
    return searchCount < SEARCH_LIMIT
  }

  // Increment search count and check limit
  const incrementSearchCount = () => {
    if (user) return true // Logged in users don't need counting

    const newCount = searchCount + 1
    setSearchCount(newCount)
    
    // Store in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, newCount.toString())
    }

    // Show modal when they've used all their searches (on 3rd attempt)
    if (newCount > SEARCH_LIMIT) {
      setIsLimitReached(true)
      setShowLoginModal(true)
      return false
    }
    
    return true
  }

  // Check if search would exceed limit (for preview before action)
  const wouldExceedLimit = () => {
    if (user) return false
    return searchCount >= SEARCH_LIMIT
  }

  // Get remaining searches
  const getRemainingSearches = () => {
    if (user) return Infinity
    return Math.max(0, SEARCH_LIMIT - searchCount)
  }

  // Handle when user tries to search but is at limit
  const handleSearchAttemptAtLimit = () => {
    if (user) return true
    
    if (searchCount >= SEARCH_LIMIT) {
      setShowLoginModal(true)
      return false
    }
    
    return incrementSearchCount()
  }

  // Reset search count (for testing purposes)
  const resetSearchCount = () => {
    setSearchCount(0)
    setIsLimitReached(false)
    setShowLoginModal(false)
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  const value = {
    searchCount,
    searchLimit: SEARCH_LIMIT,
    canSearch,
    incrementSearchCount,
    wouldExceedLimit,
    getRemainingSearches,
    isLimitReached,
    showLoginModal,
    setShowLoginModal,
    handleSearchAttemptAtLimit,
    resetSearchCount
  }

  return (
    <SearchLimitContext.Provider value={value}>
      {children}
    </SearchLimitContext.Provider>
  )
}