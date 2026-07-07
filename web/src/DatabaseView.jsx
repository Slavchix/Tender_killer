import { useEffect, useState } from 'react'
import { Database, Search } from 'lucide-react'
import { fetchDatabaseTable, fetchDatabaseTables } from './api'
import { formatDbCell } from './formatters'

export function DatabaseView() {
  const [tables, setTables] = useState([])
  const [selectedTable, setSelectedTable] = useState('tenders')
  const [tableData, setTableData] = useState({ columns: [], rows: [], total: 0 })
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDatabaseTables()
      .then((payload) => {
        const nextTables = payload.tables || []
        setTables(nextTables)
        setSelectedTable((current) => current || nextTables[0]?.name || 'tenders')
      })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedTable) return
    const params = new URLSearchParams({ limit: '100' })
    if (query.trim()) params.set('q', query.trim())
    setLoading(true)
    setError('')
    fetchDatabaseTable(selectedTable, params)
      .then(setTableData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedTable, query])

  return (
    <section className="database-view">
      <aside className="database-sidebar">
        <div className="panel-title"><Database size={18} /> SQLite</div>
        <div className="table-tabs">
          {tables.map((table) => (
            <button
              className={selectedTable === table.name ? 'active' : ''}
              key={table.name}
              onClick={() => setSelectedTable(table.name)}
              type="button"
            >
              <span>{table.name}</span>
              <strong>{table.rows}</strong>
            </button>
          ))}
        </div>
      </aside>

      <section className="database-table-panel">
        <div className="database-toolbar">
          <div>
            <h2>{selectedTable}</h2>
            <span>{tableData.total || 0} строк, показаны первые {tableData.rows?.length || 0}</span>
          </div>
          <div className="input-with-icon db-search">
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Поиск по таблице" />
          </div>
        </div>
        {error && <div className="error-box">{error}</div>}
        <div className="db-table-wrap">
          <table className="db-table">
            <thead>
              <tr>
                {tableData.columns.map((column) => <th key={column}>{column}</th>)}
              </tr>
            </thead>
            <tbody>
              {(tableData.rows || []).map((row, index) => (
                <tr key={`${selectedTable}-${index}`}>
                  {tableData.columns.map((column) => (
                    <td key={column}>{formatDbCell(row[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !tableData.rows?.length && <div className="empty-state compact">Строки не найдены</div>}
          {loading && <div className="empty-state compact">Загрузка таблицы...</div>}
        </div>
      </section>
    </section>
  )
}
