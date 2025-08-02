'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, 
  Clock,
  Filter,
  X,
  Book,
  Music,
  AlertCircle,
  Trash2
} from 'lucide-react'
import { Button } from './ui/button'
import { useAuth } from '@/contexts/AuthContext'
import UserProfile from './auth/UserProfile'
import LoginButton from './auth/LoginButton'

// SVG Icon Component - simplified to avoid gradient conflicts
const SidebarIcon = ({ className = "", isCollapsed = false }) => {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path 
        d="M6.83496 3.99992C6.38353 4.00411 6.01421 4.0122 5.69824 4.03801C5.31232 4.06954 5.03904 4.12266 4.82227 4.20012L4.62207 4.28606C4.18264 4.50996 3.81498 4.85035 3.55859 5.26848L3.45605 5.45207C3.33013 5.69922 3.25006 6.01354 3.20801 6.52824C3.16533 7.05065 3.16504 7.71885 3.16504 8.66301V11.3271C3.16504 12.2712 3.16533 12.9394 3.20801 13.4618C3.25006 13.9766 3.33013 14.2909 3.45605 14.538L3.55859 14.7216C3.81498 15.1397 4.18266 15.4801 4.62207 15.704L4.82227 15.79C5.03904 15.8674 5.31234 15.9205 5.69824 15.9521C6.01398 15.9779 6.383 15.986 6.83398 15.9902L6.83496 3.99992ZM18.165 11.3271C18.165 12.2493 18.1653 12.9811 18.1172 13.5702C18.0745 14.0924 17.9916 14.5472 17.8125 14.9648L17.7295 15.1415C17.394 15.8 16.8834 16.3511 16.2568 16.7353L15.9814 16.8896C15.5157 17.1268 15.0069 17.2285 14.4102 17.2773C13.821 17.3254 13.0893 17.3251 12.167 17.3251H7.83301C6.91071 17.3251 6.17898 17.3254 5.58984 17.2773C5.06757 17.2346 4.61294 17.1508 4.19531 16.9716L4.01855 16.8896C3.36014 16.5541 2.80898 16.0434 2.4248 15.4169L2.27051 15.1415C2.03328 14.6758 1.93158 14.167 1.88281 13.5702C1.83468 12.9811 1.83496 12.2493 1.83496 11.3271V8.66301C1.83496 7.74072 1.83468 7.00898 1.88281 6.41985C1.93157 5.82309 2.03329 5.31432 2.27051 4.84856L2.4248 4.57317C2.80898 3.94666 3.36012 3.436 4.01855 3.10051L4.19531 3.0175C4.61285 2.83843 5.06771 2.75548 5.58984 2.71281C6.17898 2.66468 6.91071 2.66496 7.83301 2.66496H12.167C13.0893 2.66496 13.821 2.66468 14.4102 2.71281C15.0069 2.76157 15.5157 2.86329 15.9814 3.10051L16.2568 3.25481C16.8833 3.63898 17.394 4.19012 17.7295 4.84856L17.8125 5.02531C17.9916 5.44285 18.0745 5.89771 18.1172 6.41985C18.1653 7.00898 18.165 7.74072 18.165 8.66301V11.3271ZM8.16406 15.995H12.167C13.1112 15.995 13.7794 15.9947 14.3018 15.9521C14.8164 15.91 15.1308 15.8299 15.3779 15.704L15.5615 15.6015C15.9797 15.3451 16.32 14.9774 16.5439 14.538L16.6299 14.3378C16.7074 14.121 16.7605 13.8478 16.792 13.4618C16.8347 12.9394 16.835 12.2712 16.835 11.3271V8.66301C16.835 7.71885 16.8347 7.05065 16.792 6.52824C16.7605 6.14232 16.7073 5.86904 16.6299 5.65227L16.5439 5.45207C16.32 5.01264 15.9796 4.64498 15.5615 4.3886L15.3779 4.28606C15.1308 4.16013 14.8165 4.08006 14.3018 4.03801C13.7794 3.99533 13.1112 3.99504 12.167 3.99504H8.16406C8.16407 3.99667 8.16504 3.99829 8.16504 3.99992L8.16406 15.995Z" 
        fill={isCollapsed ? "#ec4899" : "#1f2937"}
        strokeWidth="0.5"
        stroke={isCollapsed ? "#ec4899" : "#1f2937"}
      />
    </svg>
  )
}

// Function to get work type icon based on search results
const getWorkTypeIcon = (search, className) => {
  // Check if the search has results and determine predominant work type
  if (search.results && search.results.length > 0) {
    const workTypes = search.results.map(result => result.category || result.work_type);
    const literatureCount = workTypes.filter(type => type === 'Literature' || type === 'literary').length;
    const musicCount = workTypes.filter(type => type === 'Music' || type === 'musical').length;
    
    if (literatureCount > musicCount) {
      return <Book className={className} />;
    } else if (musicCount > 0) {
      return <Music className={className} />;
    }
  }
  
  // Default to book icon for unknown or mixed results
  return <Book className={className} />;
}

export default function SearchHistorySidebar({ onSearchHistoryClick, onToggleCollapse, isMobileOpen = false, onMobileToggle }) {
  const { user, getSearchHistory, deleteSearchHistory } = useAuth()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [searchHistory, setSearchHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [groupedHistory, setGroupedHistory] = useState({})
  const [deletingId, setDeletingId] = useState(null)

  // Handle toggle and notify parent
  const handleToggle = () => {
    // On mobile, close the sidebar instead of toggling collapse
    if (window.innerWidth < 768 && isMobileOpen) {
      handleMobileToggle()
      return
    }
    
    // On desktop, toggle collapse normally
    const newCollapsed = !isCollapsed
    setIsCollapsed(newCollapsed)
    if (onToggleCollapse) {
      onToggleCollapse(newCollapsed)
    }
  }

  // Handle mobile toggle
  const handleMobileToggle = () => {
    if (onMobileToggle) {
      onMobileToggle(!isMobileOpen)
    }
  }

  // Load search history when user is authenticated
  useEffect(() => {
    if (user) {
      loadSearchHistory()
    } else {
      setSearchHistory([])
      setGroupedHistory({})
    }
  }, [user])

  const loadSearchHistory = async () => {
    if (!user) return
    
    setLoading(true)
    try {
      const { data, error } = await getSearchHistory(50)
      
      if (error) {
        console.error('Error loading search history:', error)
      } else {
        const history = data || []
        setSearchHistory(history)
        groupHistoryByDate(history)
      }
    } catch (error) {
      console.error('Failed to load search history:', error)
    } finally {
      setLoading(false)
    }
  }

  const groupHistoryByDate = (history) => {
    const grouped = {}
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const lastWeek = new Date(today)
    lastWeek.setDate(lastWeek.getDate() - 7)

    history.forEach(search => {
      const searchDate = new Date(search.searched_at)
      let groupKey = 'Older'

      if (searchDate.toDateString() === today.toDateString()) {
        groupKey = 'Today'
      } else if (searchDate.toDateString() === yesterday.toDateString()) {
        groupKey = 'Yesterday'
      } else if (searchDate >= lastWeek) {
        groupKey = 'Last 7 days'
      } else {
        groupKey = 'Older'
      }

      if (!grouped[groupKey]) {
        grouped[groupKey] = []
      }
      grouped[groupKey].push(search)
    })

    setGroupedHistory(grouped)
  }

  const handleHistoryClick = (search) => {
    if (onSearchHistoryClick) {
      onSearchHistoryClick(search)
    }
    // Close mobile sidebar after selection
    if (isMobileOpen && onMobileToggle) {
      onMobileToggle(false)
    }
  }

  const handleDeleteHistory = async (e, searchId) => {
    e.stopPropagation() // Prevent triggering the history click
    
    if (!user || !searchId) return
    
    setDeletingId(searchId)
    
    try {
      const { error } = await deleteSearchHistory(searchId)
      
      if (error) {
        console.error('Failed to delete search history:', error)
        // You can add a toast notification here if you have one
      } else {
        // Remove from local state immediately for better UX
        setSearchHistory(prev => prev.filter(item => item.id !== searchId))
        // Reload the full history to sync with database
        await loadSearchHistory()
      }
    } catch (error) {
      console.error('Failed to delete search history:', error)
    } finally {
      setDeletingId(null)
    }
  }

  const formatFilters = (filters) => {
    if (!filters || Object.keys(filters).length === 0) return null
    
    const filterArray = []
    if (filters.category && filters.category !== 'All') filterArray.push(filters.category)
    if (filters.country && filters.country !== 'All') filterArray.push(filters.country)
    if (filters.status && filters.status !== 'All') filterArray.push(filters.status)
    
    return filterArray.length > 0 ? filterArray.join(', ') : null
  }

  const truncateQuery = (query, maxLength = 30) => {
    return query.length > maxLength ? query.substring(0, maxLength) + '...' : query
  }

  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={handleMobileToggle}
        className="md:hidden fixed top-10 left-4 z-50 bg-white shadow-lg rounded-full p-2 border border-gray-200"
      >
        <SidebarIcon className="w-5 h-5" isCollapsed={true} />
      </button>
      
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-gray-100 bg-opacity-60 backdrop-blur-sm z-30"
          onClick={handleMobileToggle}
        />
      )}
      
      <div className={`fixed left-0 top-0 h-screen bg-white border-r border-gray-200 flex flex-col transition-all duration-300 z-40 shadow-sm ${
        isCollapsed ? 'w-12 md:w-12' : 'w-[85%] md:w-80'
      } ${isMobileOpen ? 'translate-x-0 z-50' : '-translate-x-full md:translate-x-0 z-40'}`}>
        {/* Header with toggle */}
        <div className="py-3 border-b border-gray-200 flex items-center justify-between">
          {!isCollapsed && (
            <h2 className="p-3 text-sm font-semibold text-gray-900">Search History</h2>
          )}
          <button
            onClick={handleToggle}
            className={`p-1.5 hover:bg-gray-100 rounded-md transition-colors ${isCollapsed ? 'mx-auto' : ''}`}
          >
            {isCollapsed ? (
              <SidebarIcon className="w-5 h-5" isCollapsed={true} />
            ) : (
              <X className="h-4 w-4 mx-1 text-gray-500" />
            )}
          </button>
        </div>
        
        {/* Profile Section for non-authenticated users */}
        {!user && (
          <div className="p-3">
            {isCollapsed ? (
              <div className="flex justify-center">
                <SidebarIcon className="w-5 h-5" isCollapsed={false} />
              </div>
            ) : (
              <div className="text-center bg-gray-50 rounded-lg p-4">
                <SidebarIcon className="mx-auto mb-3 w-8 h-8" isCollapsed={false} />
                <p className="text-gray-600 font-medium mb-2 text-sm">Sign in to access</p>
                <p className="text-xs text-gray-500 mb-3">Track your search history</p>
                <LoginButton />
              </div>
            )}
          </div>
        )}
        
        {/* Content */}
        {user && (
          <div className="flex-1 overflow-y-auto scrollbar-hide">
            {loading ? (
              <div className="p-3">
                {isCollapsed ? (
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand-pink"></div>
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-pink mx-auto mb-3"></div>
                    <p className="text-gray-600 text-xs">Loading...</p>
                  </div>
                )}
              </div>
            ) : searchHistory.length === 0 ? (
              <div className="p-3">
                {isCollapsed ? (
                  <div className="flex justify-center">
                    <SidebarIcon className="w-4 h-4" isCollapsed={false} />
                  </div>
                ) : (
                  <div className="text-center">
                    <SidebarIcon className="mx-auto mb-3 w-8 h-8" isCollapsed={false} />
                    <p className="text-gray-600 font-medium mb-1 text-xs">No history yet</p>
                    <p className="text-xs text-gray-500">Searches appear here</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-2">
                {Object.entries(groupedHistory).map(([groupName, searches]) => (
                  <div key={groupName} className="mb-4">
                    {!isCollapsed && (
                      <h3 className="text-xs font-medium text-gray-500 mb-2 px-2">
                        {groupName}
                      </h3>
                    )}
                    
                    <div className="space-y-1">
                      {searches.map((search) => (
                        <div
                          key={search.id}
                          onClick={() => handleHistoryClick(search)}
                          className={`cursor-pointer group transition-colors duration-200 rounded-md hover:bg-gray-50 border border-transparent hover:border-gray-200 ${
                            isCollapsed ? 'p-2' : 'p-3'
                          }`}
                        >
                          {isCollapsed ? (
                            <div className="flex justify-center">
                              {getWorkTypeIcon(search, "h-4 w-4 text-gray-400 group-hover:text-brand-pink transition-colors")}
                            </div>
                          ) : (
                            <div className="flex items-start gap-2">
                              {getWorkTypeIcon(search, "h-3.5 w-3.5 text-gray-400 mt-0.5 flex-shrink-0")}
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-gray-900 truncate group-hover:text-brand-pink transition-colors leading-tight">
                                  {truncateQuery(search.query_text?.replace(/^(title:\s*|author:\s*)+/gi, '').trim() || search.query_text, 22)}
                                </p>
                                <div className="flex items-center justify-between mt-1">
                                  <span className="text-xs text-gray-500">
                                    {search.result_count} results
                                  </span>
                                  <span className="text-xs text-gray-400">
                                    {new Date(search.searched_at).toLocaleDateString(undefined, {
                                      month: 'short',
                                      day: 'numeric'
                                    })}
                                  </span>
                                </div>
                                {formatFilters(search.filters) && (
                                  <div className="mt-1">
                                    <span className="text-xs text-brand-pink bg-pink-50 px-2 py-0.5 rounded-full">
                                      {formatFilters(search.filters).substring(0, 12)}{formatFilters(search.filters).length > 12 ? '...' : ''}
                                    </span>
                                  </div>
                                )}
                              </div>
                              {/* Delete button */}
                              <button
                                onClick={(e) => handleDeleteHistory(e, search.id)}
                                disabled={deletingId === search.id}
                                className="p-1 hover:bg-red-50 rounded text-gray-400 hover:text-red-500 flex-shrink-0 transition-colors duration-200"
                                title="Delete search"
                              >
                                {deletingId === search.id ? (
                                  <div className="animate-spin h-3 w-3 border border-current border-t-transparent rounded-full"></div>
                                ) : (
                                  <Trash2 className="h-3 w-3" />
                                )}
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Profile Section */}
        {user && (
          <div className="border-t border-gray-200">
            {!isCollapsed && (
              <UserProfile />
            )}
            {isCollapsed && (
              <div className="p-2 flex justify-center">
                <div className="w-8 h-8 bg-gradient-to-br from-brand-pink to-brand-purple rounded-full flex items-center justify-center">
                  <span className="text-xs font-semibold text-white">
                    {user?.user_metadata?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U'}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Refresh Button */}
        {user && !isCollapsed && searchHistory.length > 0 && (
          <div className="p-2 border-t border-gray-200">
            <button
              onClick={loadSearchHistory}
              className="w-full text-xs text-gray-600 hover:text-brand-pink transition-colors py-1.5"
            >
              Refresh History
            </button>
          </div>
        )}
      </div>
    </>
  )
}