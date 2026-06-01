import { useState } from 'react'
import { AnalysisDecisionBrief } from './TenderAnalysisDecisionBrief'
import { AnalysisDocumentsPanel } from './TenderAnalysisDocumentsPanel'
import { AnalysisEvidencePanel } from './TenderAnalysisEvidencePanel'
import { AnalysisPassport } from './TenderAnalysisPassport'
import {
  AnalysisSectionBody,
  AnalysisSectionRail,
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
  const [selectedAnalysisSection, setSelectedAnalysisSection] = useState('blockers')
  const analysisSections = analysisSectionItems(analysis, documents)
  const analysisActionDisabled = preparingAnalysis || downloading || extracting || analyzing

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
      <AnalysisPassport analysis={analysis} />
      <AnalysisSummary analysis={analysis} documents={documents} />
      <AnalysisDecisionBrief
        analysis={analysis}
        documents={documents}
        onOpenSection={setSelectedAnalysisSection}
      />

      <div className="analysis-workspace">
        <AnalysisSectionRail
          sections={analysisSections}
          selectedSection={selectedAnalysisSection}
          onSelectSection={setSelectedAnalysisSection}
        />

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

        <AnalysisEvidencePanel documents={documents} analysis={analysis} />
      </div>
    </section>
  )
}
