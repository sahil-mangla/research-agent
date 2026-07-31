import { useEffect, useRef, useState } from "react"
import { ShootingStars } from "@/components/ui/shooting-stars"
import { StarsBackground } from "@/components/ui/stars-background"
import { getRun, startRun, type RunStatus } from "@/lib/api"

const STEPS = [
  { n: "01", label: "Expand query" },
  { n: "02", label: "Retrieve papers" },
  { n: "03", label: "Rank relevance" },
  { n: "04", label: "Extract gaps" },
  { n: "05", label: "Synthesize themes" },
  { n: "06", label: "Write briefs" },
]

const TERMINAL_DOT_COUNT = 5

function formatElapsed(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, "0")}`
}

function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={`inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent opacity-80 ${className ?? ""}`}
      aria-hidden="true"
    />
  )
}

function App() {
  const [problemStatement, setProblemStatement] = useState("")
  const [job, setJob] = useState<RunStatus | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const isRunning = job?.status === "running"

  const [autoStepIdx, setAutoStepIdx] = useState(0)
  const [hoveredStepIdx, setHoveredStepIdx] = useState<number | null>(null)
  const activeIdx = isRunning ? job.stage : (hoveredStepIdx ?? autoStepIdx)

  const [isTerminalHovered, setIsTerminalHovered] = useState(false)
  const [terminalDotIdx, setTerminalDotIdx] = useState(TERMINAL_DOT_COUNT - 1)

  useEffect(() => {
    if (!isTerminalHovered) return
    const id = setInterval(() => {
      setTerminalDotIdx((prev) => (prev + 1) % TERMINAL_DOT_COUNT)
    }, 500)
    return () => clearInterval(id)
  }, [isTerminalHovered])

  useEffect(() => {
    if (isRunning) return
    const id = setInterval(() => {
      setAutoStepIdx((prev) => (prev + 1) % STEPS.length)
    }, 1300)
    return () => clearInterval(id)
  }, [isRunning])

  const [elapsedSec, setElapsedSec] = useState(0)
  useEffect(() => {
    if (!isRunning) {
      setElapsedSec(0)
      return
    }
    const startedAt = Date.now()
    const id = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startedAt) / 1000))
    }, 1000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRunning, job?.job_id])

  const isFetchingRef = useRef(false)
  useEffect(() => {
    if (!isRunning || !job) return
    const jobId = job.job_id
    const id = setInterval(async () => {
      if (isFetchingRef.current) return
      isFetchingRef.current = true
      try {
        const latest = await getRun(jobId)
        setJob(latest)
      } catch (err) {
        setSubmitError(err instanceof Error ? err.message : String(err))
      } finally {
        isFetchingRef.current = false
      }
    }, 1500)
    return () => clearInterval(id)
  }, [isRunning, job])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isRunning || !problemStatement.trim()) return
    setSubmitError(null)
    try {
      const { job_id } = await startRun(problemStatement)
      setJob({
        job_id,
        status: "running",
        stage: 0,
        stage_label: STEPS[0].label,
        run_id: null,
        opportunities: null,
        error: null,
      })
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
    }
  }

  return (
    <div className="relative min-h-screen w-full overflow-x-hidden bg-[oklch(0.12_0.005_90)] font-[Inter,sans-serif] text-[oklch(0.92_0.01_90/0.9)]">
      <StarsBackground
        starDensity={0.00045}
        className="z-0"
        minTwinkleSpeed={0.6}
        maxTwinkleSpeed={1.4}
      />
      <ShootingStars
        className="z-[1]"
        starColor="oklch(0.85 0.08 60)"
        trailColor="oklch(0.72 0.1 55)"
        starWidth={12}
        starHeight={1.5}
        minSpeed={12}
        maxSpeed={22}
        minDelay={1800}
        maxDelay={5200}
      />

      <div className="relative z-10 mx-auto max-w-[1400px] px-6 sm:px-10 lg:px-16">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-[oklch(0.9_0.01_90/0.12)] py-4">
          <div className="font-['Newsreader',serif] text-[20px] tracking-[0.01em] text-[oklch(0.92_0.01_90)]">
            research-agent
          </div>
          <a
            href="https://github.com/sahil-mangla/research-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-[oklch(0.75_0.06_55/0.4)] px-4 py-2 font-['JetBrains_Mono',monospace] text-sm text-[oklch(0.8_0.07_55)] transition-colors hover:bg-[oklch(0.9_0.01_90/0.06)] hover:border-[oklch(0.75_0.06_55/0.7)]"
          >
            GitHub ↗
          </a>
        </header>

        {/* Hero */}
        <div className="grid grid-cols-1 items-center gap-8 py-8 sm:py-10 lg:grid-cols-[1.3fr_1fr] lg:py-10">
          <div className="max-w-[620px]">
            <div className="mb-4 font-['JetBrains_Mono',monospace] text-[13px] tracking-[0.14em] text-[oklch(0.78_0.07_55)]">
              RESEARCH &rarr; GAPS &rarr; OPPORTUNITY
            </div>
            <h1 className="mb-4 text-pretty font-['Newsreader',serif] text-[32px] leading-[1.14] font-medium text-[oklch(0.94_0.01_90)] sm:text-[40px] lg:text-[46px]">
              Let the research tell you what to{" "}
              <em className="border-b-2 border-[oklch(0.72_0.1_55/0.5)] italic text-[oklch(0.72_0.1_55)]">
                build
              </em>{" "}
              next.
            </h1>
            <p className="mb-6 max-w-[520px] text-pretty text-[16px] leading-[1.6] text-[oklch(0.85_0.01_90/0.75)]">
              Give it a problem. It mines real gaps from the literature —
              extracted verbatim from author-admitted limitations — and turns
              them into scoped opportunity briefs.
            </p>
            <form onSubmit={handleSubmit} className="max-w-[520px]">
              <textarea
                value={problemStatement}
                onChange={(e) => setProblemStatement(e.target.value)}
                disabled={isRunning}
                rows={2}
                placeholder="e.g. How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"
                className="mb-4 w-full resize-none rounded-lg border border-[oklch(0.9_0.01_90/0.15)] bg-[oklch(0.16_0.006_90)] px-4 py-3 font-['JetBrains_Mono',monospace] text-[13px] leading-[1.6] text-[oklch(0.9_0.01_90)] placeholder:text-[oklch(0.7_0.01_90/0.4)] focus:border-[oklch(0.72_0.1_55/0.6)] focus:outline-none disabled:opacity-60"
              />
              <div className="flex items-center gap-7">
                <button
                  type="submit"
                  disabled={isRunning || !problemStatement.trim()}
                  className="flex items-center gap-2.5 rounded-lg bg-[oklch(0.68_0.11_50)] px-7 py-3 text-[15px] font-semibold text-[oklch(0.99_0_0)] transition-colors hover:bg-[oklch(0.72_0.11_50)] disabled:cursor-not-allowed disabled:opacity-70 disabled:hover:bg-[oklch(0.68_0.11_50)]"
                >
                  {isRunning ? (
                    <>
                      <Spinner />
                      {job.stage_label}… ({formatElapsed(elapsedSec)})
                    </>
                  ) : (
                    "Get started"
                  )}
                </button>
              </div>
              {submitError && (
                <p className="mt-3 text-[13px] text-[oklch(0.65_0.18_25)]">
                  {submitError}
                </p>
              )}
            </form>
          </div>

          <div className="relative mx-auto flex w-full max-w-[440px] flex-col gap-6 py-4 lg:mx-0 lg:max-w-none lg:block lg:h-[300px] lg:py-0">
            {/* Terminal card */}
            <div
              className="z-0 w-full cursor-default overflow-hidden rounded-[10px] border border-[oklch(0.9_0.01_90/0.1)] bg-[oklch(0.16_0.006_90)] shadow-[0_30px_80px_oklch(0_0_0/0.5)] lg:absolute lg:top-0 lg:right-[10%] lg:left-0 lg:w-auto"
              onMouseEnter={() => setIsTerminalHovered(true)}
              onMouseLeave={() => {
                setIsTerminalHovered(false)
                setTerminalDotIdx(TERMINAL_DOT_COUNT - 1)
              }}
            >
              <div className="flex gap-2 border-b border-[oklch(0.9_0.01_90/0.08)] px-[18px] py-[14px]">
                <div className="h-[11px] w-[11px] rounded-full bg-[oklch(0.65_0.18_25)]" />
                <div className="h-[11px] w-[11px] rounded-full bg-[oklch(0.75_0.13_85)]" />
                <div className="h-[11px] w-[11px] rounded-full bg-[oklch(0.7_0.14_145)]" />
              </div>
              <div className="px-5 py-[22px] font-['JetBrains_Mono',monospace] text-sm leading-[1.9] text-[oklch(0.85_0.01_90/0.85)]">
                <div>
                  <span className="text-[oklch(0.72_0.1_55)]">$</span> python
                  -m agent
                </div>
                <div className="text-[oklch(0.78_0.07_55)]">
                  data drift..."
                </div>
                <div className="mt-3.5 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[oklch(0.7_0.14_145)]" />
                  <span className="text-[oklch(0.7_0.01_90/0.5)]">01</span>
                  <div className="ml-1.5 flex gap-1.5">
                    {Array.from({ length: TERMINAL_DOT_COUNT }).map((_, i) => (
                      <div
                        key={i}
                        className="h-3.5 w-3.5 rounded-full border transition-all duration-300 ease-out"
                        style={
                          i === terminalDotIdx
                            ? {
                                borderColor: "oklch(0.7 0.1 55)",
                                background: "oklch(0.7 0.1 55)",
                              }
                            : {
                                borderColor: "oklch(0.9 0.01 90 / 0.25)",
                                background: "transparent",
                              }
                        }
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Opportunity brief card */}
            <div className="relative z-[1] w-full rounded-[10px] border border-[oklch(0.9_0.01_90/0.1)] bg-[oklch(0.17_0.007_90)] px-[22px] py-6 shadow-[0_30px_80px_oklch(0_0_0/0.55)] lg:absolute lg:top-[135px] lg:right-0 lg:left-[26%] lg:w-auto">
              <div className="mb-4 flex items-start justify-between">
                <div className="font-['JetBrains_Mono',monospace] text-[11px] leading-tight tracking-[0.1em] text-[oklch(0.7_0.01_90/0.55)]">
                  OPPORTUNITY
                  <br />
                  BRIEF
                </div>
                <div className="rounded-md border border-[oklch(0.9_0.01_90/0.15)] px-2.5 py-[5px] font-['JetBrains_Mono',monospace] text-[11px] whitespace-nowrap text-[oklch(0.7_0.01_90/0.55)]">
                  Saturation: Moderate
                </div>
              </div>
              <div className="mb-[18px] font-['Newsreader',serif] text-[19px] leading-[1.45] text-[oklch(0.92_0.01_90)]">
                Streaming drift detection for memory-bounded edge deployments
              </div>
              <div className="text-[13px] text-[oklch(0.7_0.01_90/0.5)]">
                Supported by 4 papers
              </div>
            </div>
          </div>
        </div>

        {/* Steps */}
        <div
          id="steps"
          className="mt-10 border-t border-[oklch(0.9_0.01_90/0.12)] pt-6 pb-14 sm:mt-14 sm:pt-7 lg:mt-16 lg:pt-8"
        >
          <div className="mb-8 text-center font-['JetBrains_Mono',monospace] text-[13px] tracking-[0.14em] text-[oklch(0.78_0.07_55)] sm:mb-9">
            HOW IT WORKS
          </div>
          <div
            className="relative grid grid-cols-2 gap-y-9 sm:grid-cols-3 lg:grid-cols-6 lg:gap-5"
            onMouseLeave={() => setHoveredStepIdx(null)}
          >
            <div className="absolute top-[23px] right-[calc(100%/12)] left-[calc(100%/12)] hidden h-px bg-[oklch(0.9_0.01_90/0.12)] lg:block" />
            <div
              className="absolute top-[23px] left-[calc(100%/12)] hidden h-px bg-[oklch(0.72_0.1_55)] transition-[width] duration-700 ease-in-out lg:block"
              style={{
                width: `calc((100% - 100%/6) * ${activeIdx / (STEPS.length - 1)})`,
              }}
            >
              <div
                className="absolute top-1/2 right-0 h-2.5 w-2.5 -translate-y-1/2 translate-x-1/2 rounded-full"
                style={{
                  background: "oklch(0.88 0.09 60)",
                  boxShadow:
                    "0 0 12px 4px oklch(0.72 0.1 55 / 0.85), 0 0 24px 8px oklch(0.72 0.1 55 / 0.35)",
                }}
              />
            </div>
            {STEPS.map((step, i) => {
              const isActive = i === activeIdx
              return (
                <div
                  key={step.n}
                  className="cursor-default text-center"
                  onMouseEnter={() => setHoveredStepIdx(i)}
                >
                  <div
                    className="relative z-[1] mx-auto mb-3.5 flex h-[46px] w-[46px] items-center justify-center rounded-full border bg-[oklch(0.12_0.005_90)] font-['JetBrains_Mono',monospace] text-[13px] transition-all duration-200"
                    style={{
                      borderColor: isActive
                        ? "oklch(0.72 0.1 55)"
                        : "oklch(0.9 0.01 90 / 0.2)",
                      color: isActive
                        ? "oklch(0.72 0.1 55)"
                        : "oklch(0.75 0.01 90 / 0.6)",
                    }}
                  >
                    {step.n}
                  </div>
                  <div
                    className="text-[15px] transition-colors duration-200"
                    style={{
                      color: isActive
                        ? "oklch(0.94 0.01 90)"
                        : "oklch(0.85 0.01 90 / 0.75)",
                    }}
                  >
                    {step.label}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {isRunning && (
          <div
            id="results"
            className="border-t border-[oklch(0.9_0.01_90/0.12)] py-14"
          >
            <div className="mb-4 flex items-center gap-2.5 font-['JetBrains_Mono',monospace] text-[13px] tracking-[0.14em] text-[oklch(0.78_0.07_55)]">
              <Spinner />
              RESEARCHING — THIS CAN TAKE A MINUTE OR TWO (
              {formatElapsed(elapsedSec)})
            </div>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {[0, 1].map((i) => (
                <div
                  key={i}
                  className="animate-pulse rounded-[10px] border border-[oklch(0.9_0.01_90/0.1)] bg-[oklch(0.16_0.006_90)] p-6"
                >
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div className="h-3 w-24 rounded bg-[oklch(0.9_0.01_90/0.12)]" />
                    <div className="h-5 w-28 rounded-md bg-[oklch(0.9_0.01_90/0.1)]" />
                  </div>
                  <div className="mb-2 h-5 w-4/5 rounded bg-[oklch(0.9_0.01_90/0.14)]" />
                  <div className="mb-4 h-5 w-3/5 rounded bg-[oklch(0.9_0.01_90/0.14)]" />
                  <div className="mb-2 h-3 w-full rounded bg-[oklch(0.9_0.01_90/0.08)]" />
                  <div className="mb-2 h-3 w-11/12 rounded bg-[oklch(0.9_0.01_90/0.08)]" />
                  <div className="mb-4 h-3 w-2/3 rounded bg-[oklch(0.9_0.01_90/0.08)]" />
                  <div className="h-3 w-32 rounded bg-[oklch(0.9_0.01_90/0.08)]" />
                </div>
              ))}
            </div>
          </div>
        )}

        {job?.status === "error" && (
          <div
            id="results"
            className="border-t border-[oklch(0.9_0.01_90/0.12)] py-10 text-center"
          >
            <p className="mx-auto max-w-[560px] text-[15px] text-[oklch(0.65_0.18_25)]">
              Run failed: {job.error}
            </p>
          </div>
        )}

        {job?.status === "done" && job.opportunities && (
          <div
            id="results"
            className="border-t border-[oklch(0.9_0.01_90/0.12)] py-14"
          >
            <div className="mb-4 font-['JetBrains_Mono',monospace] text-[13px] tracking-[0.14em] text-[oklch(0.78_0.07_55)]">
              {job.opportunities.length} OPPORTUNIT
              {job.opportunities.length === 1 ? "Y" : "IES"} FOUND
            </div>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {job.opportunities.map((opp, i) => (
                <div
                  key={i}
                  className="rounded-[10px] border border-[oklch(0.9_0.01_90/0.1)] bg-[oklch(0.16_0.006_90)] p-6 shadow-[0_20px_60px_oklch(0_0_0/0.4)]"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div className="font-['JetBrains_Mono',monospace] text-[11px] tracking-[0.1em] text-[oklch(0.7_0.01_90/0.55)]">
                      OPPORTUNITY {String(i + 1).padStart(2, "0")}
                    </div>
                    <div className="rounded-md border border-[oklch(0.9_0.01_90/0.15)] px-2.5 py-[5px] font-['JetBrains_Mono',monospace] text-[11px] whitespace-nowrap text-[oklch(0.7_0.01_90/0.55)]">
                      {opp.saturation_check.is_saturated
                        ? "Saturation: High"
                        : "Saturation: Open"}
                    </div>
                  </div>
                  <div className="mb-3 font-['Newsreader',serif] text-[19px] leading-[1.4] text-[oklch(0.92_0.01_90)]">
                    {opp.core_problem}
                  </div>
                  <p className="mb-3 text-[14px] leading-[1.6] text-[oklch(0.85_0.01_90/0.75)]">
                    {opp.recommended_solution}
                  </p>
                  {opp.features.length > 0 && (
                    <ul className="mb-3 space-y-1">
                      {opp.features.map((f, fi) => (
                        <li
                          key={fi}
                          className="text-[13px] leading-[1.5] text-[oklch(0.85_0.01_90/0.7)]"
                        >
                          <span className="text-[oklch(0.72_0.1_55)]">
                            &middot;
                          </span>{" "}
                          {f.feature}
                        </li>
                      ))}
                    </ul>
                  )}
                  <div className="text-[13px] text-[oklch(0.7_0.01_90/0.5)]">
                    Supported by {opp.supporting_papers.length} paper
                    {opp.supporting_papers.length === 1 ? "" : "s"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <footer className="border-t border-[oklch(0.9_0.01_90/0.1)] py-5 text-center font-['JetBrains_Mono',monospace] text-[13px] text-[oklch(0.7_0.01_90/0.45)]">
          MIT licensed &middot; Built for researchers who'd rather build than
          skim.
        </footer>
      </div>
    </div>
  )
}

export default App
