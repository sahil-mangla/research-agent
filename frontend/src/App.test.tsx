import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import App from "./App"
import type { RunStatus } from "./lib/api"

describe("App", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it("disables the submit button until a problem statement is entered", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<App />)

    const button = screen.getByRole("button", { name: /get started/i })
    expect(button).toBeDisabled()

    await user.type(screen.getByPlaceholderText(/e\.g\. how can small teams/i), "test problem")
    expect(button).toBeEnabled()
  })

  it("submits a run and renders opportunities once the job completes", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    const doneStatus: RunStatus = {
      job_id: "job-1",
      status: "done",
      stage: 5,
      stage_label: "Write briefs",
      run_id: "run-1",
      opportunities: [
        {
          core_problem: "Teams lack lightweight drift detection",
          why_now: "because reasons",
          saturation_check: { obvious_solution: "dashboard", is_saturated: true, differentiation: "diff" },
          recommended_solution: "Ship a two-stage detector",
          features: [{ feature: "cheap always-on screen", supports_core_problem: "s", priority: "core" }],
          supporting_papers: [{ title: "Paper A", url: null, relevant_finding: "finding" }],
          feasibility_notes: "notes",
          recurrence_signal: "signal",
        },
      ],
      error: null,
    }

    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ job_id: "job-1" }),
    } as Response).mockResolvedValue({
      ok: true,
      json: async () => doneStatus,
    } as Response)
    vi.stubGlobal("fetch", fetchMock)

    render(<App />)
    await user.type(screen.getByPlaceholderText(/e\.g\. how can small teams/i), "test problem")
    await user.click(screen.getByRole("button", { name: /get started/i }))

    await vi.advanceTimersByTimeAsync(1500)

    await waitFor(() => {
      expect(screen.getByText(/teams lack lightweight drift detection/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/1 opportunity found/i)).toBeInTheDocument()
  })

  it("surfaces the submit error when starting a run fails", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "boom",
      } as Response),
    )

    render(<App />)
    await user.type(screen.getByPlaceholderText(/e\.g\. how can small teams/i), "test problem")
    await user.click(screen.getByRole("button", { name: /get started/i }))

    await waitFor(() => {
      expect(screen.getByText("boom")).toBeInTheDocument()
    })
  })
})
