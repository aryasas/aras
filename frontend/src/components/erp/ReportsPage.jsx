export default function ReportsPage({ initialReportId }) {
  const [reports, setReports] = useState({})
  const [search, setSearch] = useState('')
  const [activeReportId, setActiveReportId] = useState(initialReportId || null)
  const [reportData, setReportData] = useState(null)
  const [loadingReport, setLoadingReport] = useState(false)
  const [filters, setFilters] = useState({})

  // Fetch initial report list
  useEffect(() => {
    fetch('/admin/erp/reports/list.json') 
      .then(r => r.json())
      .then(data => {
        setReports(data.grouped || {})
        if (initialReportId) {
          selectReport(initialReportId)
        }
      })
  }, [initialReportId])
