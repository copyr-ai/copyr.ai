'use client'

import Image from "next/image"
import { motion } from "framer-motion"
import { Button } from "../components/ui/button"
import { useEffect, useState } from "react"
import { useAuth } from "@/contexts/AuthContext"
import LoginButton from "./auth/LoginButton"
import UserProfile from "./auth/UserProfile"

export default function Navbar({ sidebarCollapsed = null, isMobileSidebarOpen = false }) {
  const [isHidden, setIsHidden] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [isSearchPage, setIsSearchPage] = useState(false)
  const [isHomePage, setIsHomePage] = useState(false)
  const [isWorkPage, setIsWorkPage] = useState(false)
  const { user, loading } = useAuth()
  
  // Close profile dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showProfile && !event.target.closest('.profile-dropdown')) {
        setShowProfile(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showProfile])

  // Check if we're on search page, homepage, or work page
  useEffect(() => {
    const checkPage = () => {
      setIsSearchPage(window.location.pathname.startsWith('/search'))
      setIsHomePage(window.location.pathname === '/')
      setIsWorkPage(window.location.pathname.startsWith('/work'))
    }
    
    checkPage()
    window.addEventListener('popstate', checkPage)
    
    return () => window.removeEventListener('popstate', checkPage)
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY
      const viewportHeight = window.innerHeight
      
      // Check if we're on any search page (including with query parameters)
      const currentIsSearchPage = window.location.pathname.startsWith('/search')
      
      if (currentIsSearchPage) {
        // On search page, hide navbar much earlier - before searchbar area
        // Search bar area starts around 32 (pt-32) which is ~128px from top
        // Hide navbar when we scroll past 80px on search page
        setIsHidden(scrollY > 80)
        return
      }
      
      // For other pages, use the original logic
      // Check if any main content is overlapping with navbar area (top 100px)
      const contentElements = document.querySelectorAll('main, [data-main-content], .search-content, .work-content')
      let hasOverlap = false
      
      contentElements.forEach(element => {
        if (element) {
          const rect = element.getBoundingClientRect()
          // Check if content is in the navbar area (top 100px of viewport)
          if (rect.top < 100 && rect.bottom > 0) {
            hasOverlap = true
          }
        }
      })
      
      // Also check for specific containers that might indicate main content
      const searchContainer = document.querySelector('[data-search-results]')
      const workContainer = document.querySelector('.work-detail-content')
      
      if (searchContainer) {
        const rect = searchContainer.getBoundingClientRect()
        if (rect.top < 100 && rect.bottom > 0) {
          hasOverlap = true
        }
      }
      
      if (workContainer) {
        const rect = workContainer.getBoundingClientRect()
        if (rect.top < 100 && rect.bottom > 0) {
          hasOverlap = true
        }
      }
      
      // Only hide navbar when:
      // 1. We've scrolled past initial section (scrollY > 150)
      // 2. AND content is overlapping with navbar area
      const pastInitialSection = scrollY > 150
      
      setIsHidden(pastInitialSection && hasOverlap)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    // Run once on mount to set initial state
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ 
      top: 0, 
      behavior: 'smooth' 
    })
  }

  const goToHomepage = () => {
    window.location.href = '/'
  }

  const goToSearch = () => {
    window.location.href = '/search'
  }

  // Calculate navbar position based on sidebar state for search page
  const getNavbarPosition = () => {
    if (!isSearchPage || sidebarCollapsed === null) {
      return "fixed top-6 left-1/2 transform -translate-x-1/2"
    }
    
    // On search page, center in remaining space after sidebar (only on desktop)
    if (sidebarCollapsed) {
      // Collapsed sidebar: 48px (3rem) width, center in remaining space
      // Available space starts at 48px, so center is at 48px + (100vw - 48px)/2
      return "fixed top-6 left-1/2 md:left-[calc(48px+(100vw-48px)/2)] transform -translate-x-1/2"
    } else {
      // Expanded sidebar: 320px (20rem) width, center in remaining space  
      // Available space starts at 320px, so center is at 320px + (100vw - 320px)/2
      return "fixed top-6 left-1/2 md:left-[calc(320px+(100vw-320px)/2)] transform -translate-x-1/2"
    }
  }

  return (
    <motion.nav 
      initial={{ opacity: 0, y: -20 }}
      animate={{ 
        opacity: (isHidden || isMobileSidebarOpen) ? 0 : 1, 
        y: (isHidden || isMobileSidebarOpen) ? -20 : 0 
      }}
      transition={{ duration: 0.3 }}
      className={`${getNavbarPosition()} z-50 bg-white/90 backdrop-blur-md rounded-full shadow-lg border border-gray-200 overflow-visible transition-all duration-300 w-fit sm:w-auto max-w-none sm:max-w-fit ${
        isMobileSidebarOpen ? 'md:opacity-100 md:translate-y-0' : ''
      }`}
    >
      <div className="flex items-center justify-start md:justify-between px-3 sm:px-6 md:px-8 py-3 sm:py-4">
        {/* Logo */}
        <div className="flex items-center cursor-pointer hover:opacity-80 transition-opacity" onClick={goToHomepage}>
          <Image
            src="/brand-copyr.ai-light.svg"
            alt="copyr.ai"
            width={120}
            height={36}
            className="h-10 w-auto min-w-[100px] sm:h-12 md:h-10 lg:h-8"
            priority
          />
        </div>

        {/* Navigation Links - Hidden on mobile homepage, visible otherwise */}
        <div className={`items-center space-x-2 sm:space-x-4 md:space-x-8 ml-6 sm:mx-4 md:mx-12 ${isHomePage ? 'hidden sm:flex' : 'flex'}`}>
          <a href="/#features" className="text-gray-600 hover:text-gray-900 hover:font-semibold font-semibold transition-all duration-200 text-sm">Features</a>
          <a href="/#about" className="text-gray-600 hover:text-gray-900 hover:font-semibold font-semibold transition-all duration-200 text-sm">About</a>
          <a 
            href="https://linkedin.com/company/copyr-ai" 
            target="_blank" 
            rel="noopener noreferrer"
            className="hidden sm:inline text-gray-600 hover:text-gray-900 hover:font-semibold font-semibold transition-all duration-200 text-sm"
          >
            Connect
          </a>
          {!isSearchPage && (
            <Button
              onClick={goToSearch}
              className={`px-3 py-1.5 sm:px-4 sm:py-2 bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white font-semibold text-xs tracking-wide rounded-full shadow-md hover:shadow-lg transition-all duration-300 transform hover:-translate-y-0.5 h-auto group ${isWorkPage ? 'hidden sm:inline-flex' : ''}`}
            >
              <span className="hidden sm:inline">Try It Now</span>
              <span className="sm:hidden">Try</span>
              <svg 
                className="w-3 h-3 ml-1 sm:ml-1.5 animate-arrow transition-transform duration-300" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Button>
          )}
        </div>

        {/* Authentication Section - Only visible on desktop */}
        <div className="hidden md:flex items-center space-x-1 sm:space-x-2 md:space-x-4">
          {loading ? (
            <div className="text-xs sm:text-sm text-gray-600">Loading...</div>
          ) : user ? (
            <div className="relative profile-dropdown">
              <button
                onClick={() => setShowProfile(!showProfile)}
                className="rounded-full p-1 hover:bg-gray-100 transition-colors duration-200"
              >
                {user.user_metadata?.avatar_url ? (
                  <img
                    src={user.user_metadata.avatar_url}
                    alt="Profile"
                    className="w-6 h-6 sm:w-8 sm:h-8 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-brand-pink to-brand-purple rounded-full flex items-center justify-center">
                    <span className="text-xs font-semibold text-white">
                      {user.email?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
              </button>
              
              {showProfile && (
                <div className="absolute right-0 top-8 sm:top-12 w-64 sm:w-72 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden">
                  <UserProfile />
                </div>
              )}
            </div>
          ) : (
            <LoginButton className="text-xs px-3 py-1.5 sm:px-4 sm:py-2" />
          )}
        </div>

      </div>
    </motion.nav>
  )
}
