// Quick search card with filters for region, sector, and profession
import { useState } from 'react'

const QuickSearch = () => {
  // State for selected filters
  const [region, setRegion] = useState('')
  const [sector, setSector] = useState('')
  const [search, setSearch] = useState('')

  // Sample data (will be replaced with API data later)
  const regions = ['Brussels', 'Flanders', 'Wallonia']
  const sectors = ['IT', 'Finance', 'Healthcare', 'Retail', 'Industry']

  return (
    <div className="card-cefora max-w-2xl mx-auto">
      {/* Card title */}
      <h2 className="text-2xl font-bold text-cefora-violet mb-6 text-center">
        Quick Search
      </h2>

      {/* Filter inputs */}
      <div className="space-y-4">
        {/* Region and Sector in a row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Region dropdown */}
          <div>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border-2 border-secondary-lilac focus:border-cefora-violet focus:outline-none transition-colors"
            >
              <option value="">📍 Select Region</option>
              {regions.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {/* Sector dropdown */}
          <div>
            <select
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border-2 border-secondary-lilac focus:border-cefora-violet focus:outline-none transition-colors"
            >
              <option value="">💼 Select Sector</option>
              {sectors.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Search input */}
        <div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="🔍 Search Profession or Skill"
            className="w-full px-4 py-3 rounded-lg border-2 border-secondary-lilac focus:border-cefora-violet focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-col md:flex-row gap-4 mt-8">
        <button className="flex-1 btn-primary">
          Explore Dashboard →
        </button>
        <button className="flex-1 bg-accent-mint text-cefora-violet font-bold py-3 px-6 rounded-xl hover:opacity-90 transition-all duration-200">
          Ask Assistant 💬
        </button>
      </div>
    </div>
  )
}

export default QuickSearch