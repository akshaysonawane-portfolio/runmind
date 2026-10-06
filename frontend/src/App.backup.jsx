import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE = "http://localhost:8000";
const RUNNER_ID = 1;

function App() {
  const [data, setData] = useState(null);
  const [runs, setRuns] = useState([]);

  const [coachQuestion, setCoachQuestion] = useState("");
  const [coachAnswer, setCoachAnswer] = useState("");
  const [coachLoading, setCoachLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);

  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [runError, setRunError] = useState(null);


  // =========================================================
// STRAVA SYNC
// =========================================================

async function syncStrava() {
  try {
    setError(null);

    const response = await fetch(
      `${API_BASE}/strava/sync?runner_id=${RUNNER_ID}`,
      {
        method: "POST",
      }
    );

    if (!response.ok) {
      throw new Error(
        `Strava sync returned ${response.status}`
      );
    }

    const result = await response.json();

    console.log("Strava sync result:", result);

    await loadDashboard();

  } catch (err) {
    console.error("Strava sync error:", err);

    setError(
      "Unable to sync Strava activities. Please try again."
    );
  }
}
  // =========================================================
  // RACE GOAL EDITOR
  // =========================================================

  const [editingGoal, setEditingGoal] = useState(false);

  const [goalForm, setGoalForm] = useState({
    race_name: "",
    distance_km: "",
    race_date: "",
    target_time_minutes: "",
  });

  const [savingGoal, setSavingGoal] = useState(false);
  const [goalError, setGoalError] = useState(null);

  // =========================================================
  // LOAD DASHBOARD
  // =========================================================

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);
      setError(null);

      const recommendationResponse = await fetch(
        `${API_BASE}/runners/${RUNNER_ID}/recommendation`
      );

      if (!recommendationResponse.ok) {
        throw new Error(
          `Recommendation API returned ${recommendationResponse.status}`
        );
      }

      const recommendationData =
        await recommendationResponse.json();

      const runsResponse = await fetch(
        `${API_BASE}/runners/${RUNNER_ID}/runs`
      );

      if (!runsResponse.ok) {
        throw new Error(
          `Runs API returned ${runsResponse.status}`
        );
      }

      const runsData = await runsResponse.json();

      setData(recommendationData);
      setRuns(runsData);

    } catch (err) {
      console.error("Dashboard error:", err);
      setError(err.message);

    } finally {
      setLoading(false);
    }
  }

  async function askRunMind() {
  if (!coachQuestion.trim()) {
    return;
  }

  try {
    setCoachLoading(true);
    setCoachAnswer("");

    const response = await fetch(
      `${API_BASE}/runners/${RUNNER_ID}/ask`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: coachQuestion,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Coach request returned ${response.status}`
      );
    }

    const result = await response.json();

    setCoachAnswer(
      result.response || result.answer || ""
    );

  } catch (err) {
    console.error("RunMind coach error:", err);

    setCoachAnswer(
      "Sorry, I couldn't get an answer right now."
    );

  } finally {
    setCoachLoading(false);
  }
}
  // =========================================================
  // RACE GOAL EDITOR
  // =========================================================

  function openGoalEditor() {
    if (!data?.race_goal) {
      return;
    }

    setGoalError(null);

    setGoalForm({
      race_name: data.race_goal.race_name || "",
      distance_km: data.race_goal.distance_km ?? "",
      race_date: data.race_goal.race_date || "",
      target_time_minutes:
        data.race_goal.target_time_minutes ?? "",
    });

    setEditingGoal(true);
  }

  function closeGoalEditor() {
    if (savingGoal) {
      return;
    }

    setEditingGoal(false);
    setGoalError(null);
  }

  async function saveGoal() {
    try {
      setSavingGoal(true);
      setGoalError(null);

      const response = await fetch(
        `${API_BASE}/runners/${RUNNER_ID}/race-goal`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            race_name: goalForm.race_name,
            distance_km: Number(goalForm.distance_km),
            race_date: goalForm.race_date,
            target_time_minutes: Number(
              goalForm.target_time_minutes
            ),
          }),
        }
      );

      if (!response.ok) {
        const errorBody = await response.text();

        throw new Error(
          errorBody ||
            `Race goal update returned ${response.status}`
        );
      }

      const updatedGoal = await response.json();

      /*
       * Update the dashboard immediately.
       *
       * This means the user doesn't have to refresh the page
       * just to see the new race goal.
       */
      setData((previousData) => ({
        ...previousData,
        race_goal: updatedGoal,
      }));

      setEditingGoal(false);

    } catch (err) {
      console.error("Race goal update error:", err);

      setGoalError(
        "Unable to update your race goal. Please try again."
      );

    } finally {
      setSavingGoal(false);
    }
  }

  // =========================================================
  // SELECT RUN
  // =========================================================

  async function fetchRunDetails(runId) {
    console.log("================================");
    console.log("RUN CLICKED:", runId);
    console.log("================================");

    try {
      setRunError(null);

      setSelectedRun(null);
      setAiAnalysis(null);
      setAiLoading(false);

      const url =
        `${API_BASE}/runners/${RUNNER_ID}/runs/${runId}/analysis`;

      console.log("Fetching:", url);

      const response = await fetch(url);

      console.log(
        "Run analysis status:",
        response.status
      );

      if (!response.ok) {
        throw new Error(
          `Run analysis returned ${response.status}`
        );
      }

      const result = await response.json();

      console.log("Run analysis result:", result);

      setSelectedRun(result);

    } catch (err) {
      console.error(
        "Failed to fetch run details:",
        err
      );

      setRunError(
        "Unable to load this run. Check the browser console."
      );
    }
  }

  // =========================================================
  // AI ANALYSIS
  // =========================================================

  async function fetchAIAnalysis() {
    if (!selectedRun) {
      return;
    }

    const runId = selectedRun.run.id;

    console.log(
      "Generating AI analysis for run:",
      runId
    );

    try {
      setAiLoading(true);
      setAiAnalysis(null);

      const response = await fetch(
        `${API_BASE}/runners/${RUNNER_ID}/runs/${runId}/coach-analysis`,
        {
          method: "POST",
        }
      );

      console.log(
        "AI response status:",
        response.status
      );

      if (!response.ok) {
        throw new Error(
          `AI analysis returned ${response.status}`
        );
      }

      const result = await response.json();

      console.log(
        "AI analysis result:",
        result
      );

      setAiAnalysis(result.analysis);

    } catch (err) {
      console.error(
        "AI analysis error:",
        err
      );

      setAiAnalysis(
        "Unable to generate RunMind analysis right now."
      );

    } finally {
      setAiLoading(false);
    }
  }

  // =========================================================
  // CLOSE RUN DETAIL
  // =========================================================

  function closeRunDetails() {
    setSelectedRun(null);
    setAiAnalysis(null);
    setAiLoading(false);
    setRunError(null);
  }

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <div className="loading">
        <h2>Loading RunMind...</h2>
        <p>Connecting your running data</p>
      </div>
    );
  }

  // =========================================================
  // ERROR
  // =========================================================

  if (error) {
    return (
      <div className="loading">
        <h2>Unable to load RunMind</h2>
        <p>{error}</p>

        <button
          className="retry-button"
          onClick={loadDashboard}
        >
          Try again
        </button>
      </div>
    );
  }

  // =========================================================
  // DATA
  // =========================================================

  const training = data?.training || {};
  const trainingLoad = data?.training_load || {};
  const recovery = data?.recovery || {};
  const race = data?.race_goal;
  const phase = data?.training_phase || {};
  const recommendation = data?.recommendation || {};

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="header">

        <div>
          <h1>RunMind</h1>

          <p>
            Your AI running coach
          </p>
        </div>
        <button
          type="button"
          className="sync-strava-button"
          onClick={syncStrava}
        >
          ↻ Sync Strava
        </button>
        <div className="runner">
          <span>🏃</span>
          <span>Akshay</span>
        </div>

      </header>


      <main className="dashboard">

        {/* ===================================================
            TODAY'S WORKOUT
        =================================================== */}

        <section className="hero-card">

          <div>

            <p className="eyebrow">
              TODAY'S WORKOUT
            </p>

            <h2>
              {recommendation.distance_km} KM{" "}
              {recommendation.intensity === "easy"
                ? "Easy"
                : recommendation.workout_type}
            </h2>

            <p className="description">
              {recommendation.adaptation_reason}
            </p>

            <button className="hero-button">
              View workout
            </button>

          </div>

          <div className="run-icon">
            🏃‍♂️
          </div>

        </section>


        {/* ===================================================
            STATS
        =================================================== */}

        <section className="stats-grid">

          <div className="card">

            <p className="label">
              Training Load
            </p>

            <h3>
              ↓ {trainingLoad.status}
            </h3>

            <p className="muted">
              {trainingLoad.current_week_km} km this week
            </p>

          </div>


          <div className="card">

            <p className="label">
              Recovery
            </p>

            <h3>
              {recovery.score} / 100
            </h3>

            <p className="muted">
              {recovery.status}
            </p>

          </div>


          <div className="card">

            <p className="label">
              Weekly Runs
            </p>

            <h3>
              {training.runs_last_7_days}
            </h3>

            <p className="muted">
              {training.distance_last_7_days} km
            </p>

          </div>


          <div className="card">

            <p className="label">
              Longest Run
            </p>

            <h3>
              {training.longest_run_last_28_days} km
            </h3>

            <p className="muted">
              Last 28 days
            </p>

          </div>

        </section>


        {/* ===================================================
            RACE GOAL
        =================================================== */}

        {race && (

          <section className="race-card">

            <div className="race-goal-info">

              <p className="eyebrow">
                RACE GOAL
              </p>

              <h2>
                {race.race_name}
              </h2>

              <p className="muted">
                {race.distance_km} km ·{" "}
                {race.race_date}
              </p>

            </div>

            <div className="race-target">

              <p>
                Target
              </p>

              <strong>
                {formatTime(
                  race.target_time_minutes
                )}
              </strong>

              <span style={{ display: "block" }}>
                Goal Pace:{" "}
                {data?.goal_pace_min_per_km != null
                  ? `${formatPace(data.goal_pace_min_per_km)} /km`
                  : "—"}
              </span>

              <span style={{ display: "block" }}>
                {(phase.phase || "").toUpperCase()} PHASE
              </span>

            </div>

            <button
              type="button"
              className="edit-goal-button"
              onClick={openGoalEditor}
            >
              Edit Goal
            </button>

          </section>

        )}


        {/* ===================================================
            EDIT RACE GOAL
        =================================================== */}

        {editingGoal && (

          <section className="card goal-editor">

            <div className="section-header">

              <div>

                <p className="eyebrow">
                  EDIT GOAL
                </p>

                <h2>
                  Update your race goal
                </h2>

              </div>

              <button
                type="button"
                className="close-button"
                onClick={closeGoalEditor}
                disabled={savingGoal}
              >
                Cancel
              </button>

            </div>


            {goalError && (
              <div className="goal-error">
                {goalError}
              </div>
            )}


            <div className="goal-form">

              <label>
                <span>Race name</span>

                <input
                  type="text"
                  value={goalForm.race_name}
                  onChange={(event) =>
                    setGoalForm({
                      ...goalForm,
                      race_name: event.target.value,
                    })
                  }
                  placeholder="Half Marathon"
                />
              </label>


              <label>
                <span>Distance (km)</span>

                <input
                  type="number"
                  min="1"
                  step="0.1"
                  value={goalForm.distance_km}
                  onChange={(event) =>
                    setGoalForm({
                      ...goalForm,
                      distance_km: event.target.value,
                    })
                  }
                  placeholder="21.1"
                />
              </label>


              <label>
                <span>Race date</span>

                <input
                  type="date"
                  value={goalForm.race_date}
                  onChange={(event) =>
                    setGoalForm({
                      ...goalForm,
                      race_date: event.target.value,
                    })
                  }
                />
              </label>


              <label>
                <span>Target time (minutes)</span>

                <input
                  type="number"
                  min="1"
                  step="1"
                  value={goalForm.target_time_minutes}
                  onChange={(event) =>
                    setGoalForm({
                      ...goalForm,
                      target_time_minutes:
                        event.target.value,
                    })
                  }
                  placeholder="115"
                />
              </label>

            </div>


            <div className="goal-editor-actions">

              <button
                type="button"
                className="cancel-goal-button"
                onClick={closeGoalEditor}
                disabled={savingGoal}
              >
                Cancel
              </button>

              <button
                type="button"
                className="save-goal-button"
                onClick={saveGoal}
                disabled={savingGoal}
              >
                {savingGoal
                  ? "Saving..."
                  : "Save Goal"}
              </button>

            </div>

          </section>

        )}
        {/* ===================================================
            ASK RUNMIND
        =================================================== */}

        <section className="card coach-card">

          <div className="section-header">

            <div>
              <p className="eyebrow">
                RUNMIND COACH
              </p>

              <h2>
                Ask RunMind
              </h2>

              <p className="muted">
                Ask anything about your training, recovery, or race goal.
              </p>
            </div>

          </div>


          <div className="coach-input-area">

            <textarea
              value={coachQuestion}
              onChange={(event) =>
                setCoachQuestion(event.target.value)
              }
              placeholder="e.g. Should I run today?"
              rows="3"
              disabled={coachLoading}
            />

            <button
              type="button"
              className="analysis-button"
              onClick={askRunMind}
              disabled={
                coachLoading ||
                !coachQuestion.trim()
              }
            >
              {coachLoading
                ? "RunMind is thinking..."
                : "Ask RunMind"}
            </button>

          </div>


          {coachAnswer && (

            <div className="coach-answer">

              <p className="eyebrow">
                RUNMIND'S ANSWER
              </p>

              <ReactMarkdown>
                {coachAnswer}
              </ReactMarkdown>

            </div>

          )}

        </section>

        {/* ===================================================
            TRAINING SUMMARY
        =================================================== */}

        <section className="card training-summary">

          <div className="section-header">

            <div>

              <p className="eyebrow">
                TRAINING
              </p>

              <h2>
                Your recent training
              </h2>

            </div>

          </div>


          <div className="training-grid">

            <div>

              <span>
                28-day mileage
              </span>

              <strong>
                {training.distance_last_28_days} km
              </strong>

            </div>


            <div>

              <span>
                Previous week
              </span>

              <strong>
                {trainingLoad.previous_week_km} km
              </strong>

            </div>


            <div>

              <span>
                Mileage change
              </span>

              <strong>
                {trainingLoad.change_percent}%
              </strong>

            </div>


            <div>

              <span>
                Race countdown
              </span>

              <strong>
                {phase.days_to_race} days
              </strong>

            </div>

          </div>

        </section>


        {/* ===================================================
            SELECTED RUN DETAIL
            IMPORTANT: ABOVE RECENT RUNS
        =================================================== */}

        {selectedRun && (

          <section
            id="run-detail"
            className="card run-detail"
          >

            <div className="section-header">

              <div>

                <p className="eyebrow">
                  RUN DETAIL
                </p>

                <h2>
                  {formatDate(
                    selectedRun.run.date
                  )}
                </h2>

              </div>


              <button
                type="button"
                className="close-button"
                onClick={closeRunDetails}
              >
                Close
              </button>

            </div>


            {/* RUN METRICS */}

            <div className="run-detail-grid">

              <div>

                <span>
                  Distance
                </span>

                <strong>
                  {selectedRun.run.distance_km.toFixed(2)} km
                </strong>

              </div>


              <div>

                <span>
                  Duration
                </span>

                <strong>
                  {formatDuration(
                    selectedRun.run.duration_minutes
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Pace
                </span>

                <strong>
                  {formatPace(
                    selectedRun.run.average_pace
                  )} /km
                </strong>

              </div>


              <div>

                <span>
                  Heart Rate
                </span>

                <strong>
                  {selectedRun.run.average_heart_rate != null
                    ? `${Math.round(
                        selectedRun.run.average_heart_rate
                      )} bpm`
                    : "—"}
                </strong>

              </div>


              <div>

                <span>
                  Cadence
                </span>

                <strong>
                  {selectedRun.run.average_cadence != null
                    ? `${Math.round(
                        selectedRun.run.average_cadence
                      )} spm`
                    : "—"}
                </strong>

              </div>


              <div>

                <span>
                  Elevation
                </span>

                <strong>
                  {selectedRun.run.elevation_gain != null
                    ? `${Math.round(
                        selectedRun.run.elevation_gain
                      )} m`
                    : "—"}
                </strong>

              </div>


              <div>

                <span>
                  Training Load
                </span>

                <strong>
                  {selectedRun.training_load.status}
                </strong>

              </div>


              <div>

                <span>
                  Recovery
                </span>

                <strong>
                  {selectedRun.recovery.score}/100
                </strong>

              </div>

            </div>


            {/* =================================================
                AI ANALYSIS
            ================================================= */}

            <div className="ai-analysis">

              <div className="ai-analysis-header">

                <div>

                  <p className="eyebrow">
                    RUNMIND
                  </p>

                  <h2>
                    🧠 RunMind Analysis
                  </h2>

                </div>


                {!aiAnalysis && !aiLoading && (

                  <button
                    type="button"
                    className="analysis-button"
                    onClick={fetchAIAnalysis}
                  >
                    Analyze this run
                  </button>

                )}

              </div>


              {aiLoading && (

                <div className="ai-loading">

                  <div className="ai-spinner"></div>

                  <p className="muted">
                    RunMind is analyzing your run...
                  </p>

                </div>

              )}


              {aiAnalysis && (

                <div className="ai-analysis-result">

                  <ReactMarkdown>
                    {aiAnalysis}
                  </ReactMarkdown>

                </div>

              )}

            </div>

          </section>

        )}


        {/* ===================================================
            RECENT RUNS
        =================================================== */}

        <section className="card recent">

          <div className="section-header">

            <div>

              <p className="eyebrow">
                ACTIVITY
              </p>

              <h2>
                Recent Runs
              </h2>

            </div>

          </div>


          {runError && (

            <div className="run-error">
              {runError}
            </div>

          )}


          {runs.length === 0 ? (

            <p className="muted">
              No Strava runs found.
            </p>

          ) : (

            <div className="runs-list">

              {runs.map((run) => (

                <button
                  type="button"
                  className={
                    selectedRun?.run?.id === run.id
                      ? "run-row selected"
                      : "run-row"
                  }
                  key={run.id}
                  onClick={() => {
                    fetchRunDetails(run.id);
                  }}
                >

                  <span>
                    {formatDate(run.date)}
                  </span>

                  <strong>
                    {run.distance_km.toFixed(2)} km
                  </strong>

                  <span>
                    {formatPace(
                      run.average_pace
                    )} /km
                  </span>

                </button>

              ))}

            </div>

          )}

        </section>

      </main>

    </div>
  );
}


// =========================================================
// FORMAT TIME
// =========================================================

function formatTime(totalMinutes) {
  const hours = Math.floor(
    totalMinutes / 60
  );

  const minutes = Math.round(
    totalMinutes % 60
  );

  return `${hours}:${minutes
    .toString()
    .padStart(2, "0")}:00`;
}


// =========================================================
// FORMAT DATE
// =========================================================

function formatDate(dateString) {
  const date = new Date(dateString);

  return date.toLocaleDateString(
    "en-IN",
    {
      month: "short",
      day: "numeric",
    }
  );
}


// =========================================================
// FORMAT PACE
// =========================================================

function formatPace(pace) {
  const minutes = Math.floor(pace);

  const seconds = Math.round(
    (pace - minutes) * 60
  );

  return `${minutes}:${seconds
    .toString()
    .padStart(2, "0")}`;
}


// =========================================================
// FORMAT DURATION
// =========================================================

function formatDuration(totalMinutes) {
  const minutes = Math.floor(
    totalMinutes
  );

  const seconds = Math.round(
    (totalMinutes - minutes) * 60
  );

  return `${minutes}m ${seconds}s`;
}


export default App;