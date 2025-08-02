'use client'

import { useState } from 'react'
import { LogOut, User, Mail } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function UserProfile() {
  const { user, profile, signOut } = useAuth()

  const handleSignOut = async () => {
    const { error } = await signOut()
    if (error) {
      console.error('Sign out error:', error)
    }
  }

  if (!user) return null

  const displayName = profile?.full_name || user.user_metadata?.full_name || 'User'
  const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  return (
    <div className="p-2">
      {/* User Info Section */}
      <div className="flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors">
        <div className="relative">
          {user.user_metadata?.avatar_url ? (
            <img
              src={user.user_metadata.avatar_url}
              alt="Profile"
              className="w-10 h-10 rounded-full object-cover"
            />
          ) : (
            <div className="w-10 h-10 bg-gradient-to-br from-brand-pink to-brand-purple rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold text-white">
                {initials}
              </span>
            </div>
          )}
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-white rounded-full"></div>
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {displayName}
          </p>
          <p className="text-xs text-gray-500 truncate flex items-center">
            <Mail className="w-3 h-3 mr-1" />
            {user.email}
          </p>
        </div>
      </div>

      {/* Divider */}
      <div className="my-2 border-t border-gray-100"></div>

      {/* Actions */}
      <div className="space-y-1">
        <button
          onClick={handleSignOut}
          className="w-full flex items-center space-x-3 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-red-600 rounded-lg transition-colors group"
        >
          <LogOut className="w-4 h-4 group-hover:text-red-600" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  )
}