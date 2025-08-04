// Use environment variable if set, otherwise default to production for deployed apps
// and localhost for local development
const getApiBaseUrl = () => {
  // In production, always use production backend unless explicitly overridden
  if (process.env.NODE_ENV === 'production') {
    return process.env.NEXT_PUBLIC_API_URL || 'https://copyr-backend.onrender.com';
  }
  
  // In development, use localhost or override
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Search works with improved endpoint
  async searchWorks(searchParams) {
    return this.request('/api/search', {
      method: 'POST',
      body: JSON.stringify(searchParams),
    })
  }

  // Get API status
  async getStatus() {
    return this.request('/api/status')
  }

  // Get supported countries
  async getSupportedCountries() {
    return this.request('/api/countries')
  }

  // Get copyright info for a country
  async getCopyrightInfo(countryCode = 'US') {
    return this.request(`/api/copyright-info/${countryCode}`)
  }

  // Get popular works from database
  async getPopularWorks(limit = 6, filters = {}) {
    const params = new URLSearchParams({ limit: limit.toString() })
    
    if (filters.work_type) params.set('work_type', filters.work_type)
    if (filters.country) params.set('country', filters.country)
    if (filters.status) params.set('status', filters.status)
    
    return this.request(`/api/popular-works?${params.toString()}`)
  }


  // User profile endpoints
  async getUserProfile(userId) {
    return this.request(`/api/user/${userId}/profile`)
  }

  // User search history endpoints
  async saveSearchHistory(userId, searchData) {
    return this.request(`/api/user/${userId}/search-history`, {
      method: 'POST',
      body: JSON.stringify(searchData),
    })
  }

  async getUserSearchHistory(userId, limit = 20) {
    return this.request(`/api/user/${userId}/search-history?limit=${limit}`)
  }

  async deleteSearchHistoryItem(userId, searchId) {
    return this.request(`/api/user/${userId}/search-history/${searchId}`, {
      method: 'DELETE',
    })
  }

  async clearUserSearchHistory(userId) {
    return this.request(`/api/user/${userId}/search-history`, {
      method: 'DELETE',
    })
  }

  // Get autocomplete suggestions from database
  async getAutocompleteSuggestions(query = '', limit = 10) {
    const params = new URLSearchParams()
    if (query) params.set('q', query)
    params.set('limit', limit.toString())
    return this.request(`/api/autocomplete?${params.toString()}`)
  }
}

export const apiClient = new ApiClient()
export default apiClient