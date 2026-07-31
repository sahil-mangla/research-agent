export interface SaturationCheck {
  obvious_solution: string
  is_saturated: boolean
  differentiation: string
}

export interface Feature {
  feature: string
  supports_core_problem: string
  priority: "core" | "supporting" | "optional"
}

export interface SupportingPaper {
  title: string
  url: string | null
  relevant_finding: string
}

export interface Opportunity {
  core_problem: string
  why_now: string
  saturation_check: SaturationCheck
  recommended_solution: string
  features: Feature[]
  supporting_papers: SupportingPaper[]
  feasibility_notes: string
  recurrence_signal: string
}

export interface RunStatus {
  job_id: string
  status: "running" | "done" | "error"
  stage: number
  stage_label: string
  run_id: string | null
  opportunities: Opportunity[] | null
  error: string | null
}

export async function startRun(problemStatement: string): Promise<{ job_id: string }> {
  const res = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problem_statement: problemStatement }),
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Request failed (${res.status})`)
  }
  return res.json()
}

export async function getRun(jobId: string): Promise<RunStatus> {
  const res = await fetch(`/api/runs/${jobId}`)
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Request failed (${res.status})`)
  }
  return res.json()
}
