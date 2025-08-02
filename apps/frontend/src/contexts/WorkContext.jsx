'use client'

import { createContext, useContext, useState, useCallback } from 'react'

const WorkContext = createContext()

export function WorkProvider({ children }) {
  const [currentWork, setCurrentWork] = useState(null)
  const [searchHistory, setSearchHistory] = useState([])
  const [currentSearchResults, setCurrentSearchResults] = useState([])

  const storeWork = useCallback((work) => {
    console.log('WorkContext - Storing work:', work);
    setCurrentWork(work)
  }, [])

  const getWork = useCallback((id) => {
    console.log('WorkContext - Getting work for ID:', id);
    console.log('WorkContext - Current work:', currentWork);
    console.log('WorkContext - Current work ID:', currentWork?.id);
    console.log('WorkContext - Current work slug:', currentWork?.slug);
    console.log('WorkContext - Search history:', searchHistory);
    
    // Try to get from current work first
    if (currentWork && (currentWork.id === id || currentWork.slug === id)) {
      console.log('WorkContext - Found in current work');
      return currentWork
    }
    
    // Try to get from search history
    const workFromHistory = searchHistory.find(w => w.id === id || w.slug === id)
    if (workFromHistory) {
      console.log('WorkContext - Found in search history');
      return workFromHistory
    }
    
    console.log('WorkContext - No work found');
    return null
  }, [currentWork, searchHistory])

  const addToSearchHistory = useCallback((works) => {
    if (Array.isArray(works)) {
      setSearchHistory(prev => {
        const combined = [...prev, ...works]
        // Remove duplicates based on id
        const unique = combined.filter((work, index, arr) => 
          arr.findIndex(w => w.id === work.id) === index
        )
        // Keep only the last 100 works to avoid memory issues
        return unique.slice(-100)
      })
    }
  }, [])

  const storeSearchResults = useCallback((results) => {
    console.log('WorkContext - Storing current search results:', results);
    setCurrentSearchResults(results || []);
  }, [])

  const getCurrentSearchResults = useCallback(() => {
    console.log('WorkContext - Getting current search results:', currentSearchResults);
    return currentSearchResults;
  }, [currentSearchResults])

  const clearWork = useCallback(() => {
    setCurrentWork(null)
  }, [])

  return (
    <WorkContext.Provider value={{
      currentWork,
      searchHistory,
      currentSearchResults,
      storeWork,
      getWork,
      addToSearchHistory,
      storeSearchResults,
      getCurrentSearchResults,
      clearWork
    }}>
      {children}
    </WorkContext.Provider>
  )
}

export function useWork() {
  const context = useContext(WorkContext)
  if (!context) {
    throw new Error('useWork must be used within a WorkProvider')
  }
  return context
}