import { useEffect, useState } from 'react'
import { AnalysisDecisionBrief } from './TenderAnalysisDecisionBrief'
import { AnalysisDocumentsPanel } from './TenderAnalysisDocumentsPanel'
import { AnalysisPassport } from './TenderAnalysisPassport'
import {
  AnalysisSectionBody,
  analysisSectionItems,
} from './TenderAnalysisSections'
import { AnalysisSummary } from './TenderAnalysisSummary'

export function TenderAnalysisTab({
  analysis,
  analyzing,
  preparingAnalysis,
  downloading,
  extracting,
  onAnalyze,
  onPrepareAnalysis,
  onDownload,
  onExtract,
  reportHref,
  documents = [],
}) {
  const [selectedAnalysisSection, setSelectedAnalysisSection] = useState('decision_risks')
  const analysisSections = analysisSectionItems(analysis, documents)
  const analysisActionDisabled = preparingAnalysis || downloading || extracting || analyzing
  const primarySection = analysis?.operator_view?.decision_brief?.primary_section

  useEffect(() => {
    const sectionIds = new Set(analysisSections.map((section) => section.id))
    if (primarySection && sectionIds.has(primarySection)) {
      setSelectedAnalysisSection(primarySection)
      return
    }
    if (!sectionIds.has(selectedAnalysisSection)) {
      setSelectedAnalysisSection(analysisSections[0]?.id || 'decision_risks')
    }
  }, [analysisSections, primarySection, selectedAnalysisSection])

  return (
    <section className="detail-section active analysis-section">
      <div className="section-heading-row analysis-action-row">
        <div>
          <h3>Анализ ТЗ</h3>
          <p className="muted-text">Риски, требования и доказательства из документов.</p>
        </div>
        <div className="analysis-actions">
          <button className="primary-button compact" disabled={analysisActionDisabled} onClick={onPrepareAnalysis} type="button">
            {preparingAnalysis ? 'Готовлю...' : 'Подготовить анализ'}
          </button>
          <button className="secondary-button compact" disabled={analysisActionDisabled} onClick={onAnalyze} type="button">
            {analyzing ? 'Анализ...' : 'Проанализировать'}
          </button>
          <a className="secondary-link-button compact" href={reportHref}>
            Скачать Word
          </a>
        </div>
      </div>

      <AnalysisDocumentsPanel
        documents={documents}
        preparing={preparingAnalysis}
        downloading={downloading}
        extracting={extracting}
        onDownload={onDownload}
        onExtract={onExtract}
      />
      <AnalysisSummary analysis={analysis} documents={documents} />
      <AnalysisDecisionBrief
        analysis={analysis}
        documents={documents}
        onOpenSection={setSelectedAnalysisSection}
      />
      <AnalysisPassport
        analysis={analysis}
        sections={analysisSections}
        selectedSection={selectedAnalysisSection}
        onSelectSection={setSelectedAnalysisSection}
      />

      <div className="analysis-workspace">
        <div className="analysis-main-panel">
          {analysis ? (
            <AnalysisSectionBody
              sectionId={selectedAnalysisSection}
              analysis={analysis}
              documents={documents}
            />
          ) : (
            <p className="muted-text">Сначала извлеки текст документов, затем запусти анализ ТЗ.</p>
          )}
        </div>

      </div>
    </section>
  )
}
