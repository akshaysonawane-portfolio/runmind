import { useEffect, useState } from "react";

import ReactMarkdown from "react-markdown";

import "./App.css";



const API_BASE = "http://localhost:8000";



function App() {

  const [data, setData] = useState(null);

  const [runs, setRuns] = useState([]);



  // =========================================================

  // AUTHENTICATION

  // =========================================================



  const [token, setToken] = useState(

    localStorage.getItem("access_token")

  );



  const [runnerId, setRunnerId] = useState(null);

  const [runnerName, setRunnerName] = useState("");



    // =========================================================

  // ONBOARDING

  // =========================================================



  const [showOnboarding, setShowOnboarding] = useState(false);



  const [profileForm, setProfileForm] = useState({

    name: "",

    age: "",

    weekly_mileage: "",

    runs_per_week: "",

  });



  const [raceForm, setRaceForm] = useState({

    race_name: "",

    distance_km: "",

    race_date: "",

    target_time_minutes: "",

  });



  const [onboardingLoading, setOnboardingLoading] =

    useState(false);



  const [onboardingError, setOnboardingError] =

    useState(null);

  const [loginEmail, setLoginEmail] = useState("");

  const [loginPassword, setLoginPassword] = useState("");

  const [loginError, setLoginError] = useState(null);

  const [loginLoading, setLoginLoading] = useState(false);



  const [coachQuestion, setCoachQuestion] = useState("");

  const [coachAnswer, setCoachAnswer] = useState("");

  const [coachLoading, setCoachLoading] = useState(false);

  const [selectedRun, setSelectedRun] = useState(null);

  const [showWorkoutDetails, setShowWorkoutDetails] = useState(false);



  const [aiAnalysis, setAiAnalysis] = useState(null);

  const [aiLoading, setAiLoading] = useState(false);



  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  const [runError, setRunError] = useState(null);





  // =========================================================

  // AUTHENTICATED API

  // =========================================================



  async function apiFetch(url, options = {}) {

    const accessToken = localStorage.getItem(

      "access_token"

    );



    const headers = {

      ...(options.headers || {}),

    };



    if (accessToken) {

      headers.Authorization =

        `Bearer ${accessToken}`;

    }



    const response = await fetch(

      url,

      {

        ...options,

        headers,

      }

    );



    if (response.status === 401) {

      localStorage.removeItem(

        "access_token"

      );



      setToken(null);

      setRunnerId(null);

      setRunnerName("");

      setData(null);

      setRuns([]);

    }



    return response;

  }



  async function login() {

    try {

      setLoginLoading(true);

      setLoginError(null);



      const body = new URLSearchParams();



      body.append(

        "username",

        loginEmail

      );



      body.append(

        "password",

        loginPassword

      );



      const response = await fetch(

        `${API_BASE}/auth/login`,

        {

          method: "POST",



          headers: {

            "Content-Type":

              "application/x-www-form-urlencoded",

          },



          body: body.toString(),

        }

      );



      if (!response.ok) {

        let message =

          "Invalid email or password.";



        try {

          const errorBody =

            await response.json();



          message =

            errorBody.detail ||

            message;



        } catch {

          // Keep default error.

        }



        throw new Error(message);

      }



      const result =

        await response.json();



      localStorage.setItem(

        "access_token",

        result.access_token

      );



      setToken(

        result.access_token

      );



      setLoginPassword("");



    } catch (err) {

      console.error(

        "Login error:",

        err

      );



      setLoginError(

        err.message ||

        "Unable to login."

      );



    } finally {

      setLoginLoading(false);

    }

  }



  function logout() {

    localStorage.removeItem(

      "access_token"

    );



    setToken(null);

    setRunnerId(null);

    setRunnerName("");

    setData(null);

    setRuns([]);

    setSelectedRun(null);

    setAiAnalysis(null);

    setCoachAnswer("");

  }



  async function loadCurrentRunner() {

    const response =

      await apiFetch(

        `${API_BASE}/auth/runner`

      );



    if (!response.ok) {

      throw new Error(

        `Unable to load runner: ${response.status}`

      );

    }



    const runner =

      await response.json();



    setRunnerId(

      runner.runner_id

    );



    setRunnerName(

      runner.name || ""

    );

    if (

      runner.weekly_mileage === 0 &&

      runner.runs_per_week === 0

    ) {

      setProfileForm({

        name: runner.name || "",

        age: runner.age || "",

        weekly_mileage: "",

        runs_per_week: "",

      });



      setShowOnboarding(true);

    }

    return runner;

  }



// =========================================================

// STRAVA SYNC

// =========================================================



async function syncStrava() {

  try {

    setError(null);



    if (!runnerId) {

      throw new Error(

        "Runner profile is not loaded yet."

      );

    }



    const response = await apiFetch(

      `${API_BASE}/strava/sync?runner_id=${runnerId}`,

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

    if (!token) {

      setLoading(false);

      return;

    }



    initializeApp();

  }, [token]);



  async function initializeApp() {

    try {

      setLoading(true);

      setError(null);



      const runner =

        await loadCurrentRunner();



      await loadDashboard(

        runner.runner_id

      );



    } catch (err) {

      console.error(

        "Initialization error:",

        err

      );



      localStorage.removeItem(

        "access_token"

      );



      setToken(null);

      setRunnerId(null);



      setError(

        "Your session has expired. Please login again."

      );



    } finally {

      setLoading(false);

    }

  }



async function loadDashboard(

  currentRunnerId = runnerId

) {

  if (!currentRunnerId) {

    return;

  }



  try {

    setLoading(true);

    setError(null);



    const recommendationResponse = await apiFetch(

      `${API_BASE}/runners/${currentRunnerId}/recommendation`

    );



    if (!recommendationResponse.ok) {

      throw new Error(

        `Recommendation API returned ${recommendationResponse.status}`

      );

    }



    const recommendationData =

      await recommendationResponse.json();



    const runsResponse = await apiFetch(

      `${API_BASE}/runners/${currentRunnerId}/runs`

    );



    if (!runsResponse.ok) {

      throw new Error(

        `Runs API returned ${runsResponse.status}`

      );

    }



    const runsData = await runsResponse.json();



    setData(recommendationData);

    setRuns(runsData);



    if (!recommendationData.race_goal) {

      setShowOnboarding(true);



      setRaceForm({

        race_name: "",

        distance_km: "",

        race_date: "",

        target_time_minutes: "",

      });

    }



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



    const response = await apiFetch(

      `${API_BASE}/runners/${runnerId}/ask`,

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



      const response = await apiFetch(

        `${API_BASE}/runners/${runnerId}/race-goal`,

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

        `${API_BASE}/runners/${runnerId}/runs/${runId}/analysis`;



      console.log("Fetching:", url);



      const response = await apiFetch(url);



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



      const response = await apiFetch(

        `${API_BASE}/runners/${runnerId}/runs/${runId}/coach-analysis`,

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

  // LOGIN

  // =========================================================



  if (!token) {

    return (

      <div className="loading">



        <h1>

          RunMind

        </h1>



        <p>

          Your AI running coach

        </p>



        <form

          onSubmit={(event) => {

            event.preventDefault();

            login();

          }}



          style={{

            width: "320px",

            margin: "30px auto",

            display: "flex",

            flexDirection: "column",

            gap: "12px",

          }}

        >



          <input

            type="email"

            placeholder="Email"

            value={loginEmail}



            onChange={(event) =>

              setLoginEmail(

                event.target.value

              )

            }



            autoComplete="email"

            required

          />



          <input

            type="password"

            placeholder="Password"

            value={loginPassword}



            onChange={(event) =>

              setLoginPassword(

                event.target.value

              )

            }



            autoComplete="current-password"

            required

          />



          {loginError && (

            <p style={{

              color: "red"

            }}>

              {loginError}

            </p>

          )}



          <button

            type="submit"

            disabled={loginLoading}

          >

            {loginLoading

              ? "Logging in..."

              : "Login"}

          </button>



        </form>



      </div>

    );

  }

// =========================================================

// ONBOARDING

// =========================================================



if (showOnboarding) {

  return (

    <div className="loading">



      <div

        style={{

          width: "500px",

          maxWidth: "90%",

          margin: "40px auto",

          padding: "30px",

          background: "white",

          borderRadius: "16px",

          boxShadow: "0 4px 20px rgba(0,0,0,0.08)",

          textAlign: "left",

        }}

      >



        <h1

          style={{

            textAlign: "center",

            marginBottom: "8px",

          }}

        >

          Welcome to RunMind 🏃

        </h1>



        <p

          style={{

            textAlign: "center",

            marginBottom: "30px",

          }}

        >

          Let's set up your running profile

        </p>



        <h3>Running Profile</h3>



        <input

          type="text"

          placeholder="Name"

          value={profileForm.name}

          onChange={(event) =>

            setProfileForm({

              ...profileForm,

              name: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "12px",

          }}

        />



        <input

          type="number"

          placeholder="Age"

          value={profileForm.age}

          onChange={(event) =>

            setProfileForm({

              ...profileForm,

              age: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "12px",

          }}

        />



        <input

          type="number"

          placeholder="Weekly mileage (km)"

          value={profileForm.weekly_mileage}

          onChange={(event) =>

            setProfileForm({

              ...profileForm,

              weekly_mileage: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "12px",

          }}

        />



        <input

          type="number"

          placeholder="Runs per week"

          value={profileForm.runs_per_week}

          onChange={(event) =>

            setProfileForm({

              ...profileForm,

              runs_per_week: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "24px",

          }}

        />



        <h3>Race Goal</h3>



        <input

          type="text"

          placeholder="Race name"

          value={raceForm.race_name}

          onChange={(event) =>

            setRaceForm({

              ...raceForm,

              race_name: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "12px",

          }}

        />



        <input

          type="number"

          step="0.1"

          placeholder="Race distance (km)"

          value={raceForm.distance_km}

          onChange={(event) =>

            setRaceForm({

              ...raceForm,

              distance_km: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "12px",

          }}

        />



        <input

          type="date"

          value={raceForm.race_date}

          onChange={(event) =>

            setRaceForm({

              ...raceForm,

              race_date: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "12px",

          }}

        />



        <input

          type="number"

          placeholder="Target time (minutes)"

          value={raceForm.target_time_minutes}

          onChange={(event) =>

            setRaceForm({

              ...raceForm,

              target_time_minutes: event.target.value,

            })

          }

          style={{

            width: "100%",

            padding: "12px",

            marginBottom: "20px",

          }}

        />



        {onboardingError && (

          <p

            style={{

              color: "red",

              marginBottom: "15px",

            }}

          >

            {onboardingError}

          </p>

        )}



        <button

          type="button"

          disabled={onboardingLoading}

          onClick={async () => {

            try {

              setOnboardingLoading(true);

              setOnboardingError(null);



              // Update runner profile

              const profileResponse =

                await apiFetch(

                  `${API_BASE}/runners/${runnerId}`,

                  {

                    method: "PUT",



                    headers: {

                      "Content-Type":

                        "application/json",

                    },



                    body: JSON.stringify({

                      name: profileForm.name,

                      age: Number(profileForm.age),

                      weekly_mileage:

                        Number(

                          profileForm.weekly_mileage

                        ),

                      runs_per_week:

                        Number(

                          profileForm.runs_per_week

                        ),

                    }),

                  }

                );



              if (!profileResponse.ok) {

                const errorBody =

                  await profileResponse.json();



                throw new Error(

                  errorBody.detail ||

                  "Failed to update profile."

                );

              }



              // Create race goal

              const raceResponse =

                await apiFetch(

                  `${API_BASE}/runners/${runnerId}/race-goal`,

                  {

                    method: "PUT",



                    headers: {

                      "Content-Type":

                        "application/json",

                    },



                    body: JSON.stringify({

                      race_name:

                        raceForm.race_name,



                      distance_km:

                        Number(

                          raceForm.distance_km

                        ),



                      race_date:

                        raceForm.race_date,



                      target_time_minutes:

                        Number(

                          raceForm.target_time_minutes

                        ),

                    }),

                  }

                );



              if (!raceResponse.ok) {

                const errorBody =

                  await raceResponse.json();



                throw new Error(

                  errorBody.detail ||

                  "Failed to create race goal."

                );

              }



              // Refresh runner information

              await loadCurrentRunner();



              setShowOnboarding(false);



              // Load the newly configured dashboard

              await loadDashboard(runnerId);



            } catch (err) {

              console.error(

                "Onboarding error:",

                err

              );



              setOnboardingError(

                err.message ||

                "Unable to complete onboarding."

              );



            } finally {

              setOnboardingLoading(false);

            }

          }}

          style={{

            width: "100%",

            padding: "14px",

            fontSize: "16px",

            fontWeight: "bold",

            cursor: "pointer",

          }}

        >

          {onboardingLoading

            ? "Setting up RunMind..."

            : "Save & Continue"}

        </button>



      </div>

    </div>

  );

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

          onClick={() => loadDashboard()}

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



          <span>

            {runnerName || "Runner"}

          </span>



          <button

            type="button"

            onClick={logout}

            style={{

              marginLeft: "12px",

            }}

          >

            Logout

          </button>



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

            <button

              type="button"

              className="hero-button"

              onClick={() => setShowWorkoutDetails(true)}

            >

              View workout <span aria-hidden="true">↗</span>

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

        {showWorkoutDetails && (

          <div

            className="workout-modal-backdrop"

            onClick={() => setShowWorkoutDetails(false)}

          >

            <section

              className="workout-modal"

              role="dialog"

              aria-modal="true"

              aria-labelledby="workout-modal-title"

              onClick={(event) => event.stopPropagation()}

            >

              <div className="workout-modal-header">

                <div>

                  <p className="eyebrow">YOUR NEXT SESSION</p>

                  <h2 id="workout-modal-title">

                    {recommendation.distance_km ?? "—"} km{" "}

                    {recommendation.intensity === "easy"

                      ? "Easy Run"

                      : recommendation.workout_type || "Run"}

                  </h2>

                </div>



                <button

                  type="button"

                  className="workout-modal-close"

                  aria-label="Close workout details"

                  onClick={() => setShowWorkoutDetails(false)}

                >

                  ×

                </button>

              </div>



              <div className="workout-detail-grid">

                <div className="workout-detail-item">

                  <span>Distance</span>

                  <strong>

                    {recommendation.distance_km ?? "—"} km

                  </strong>

                </div>



                <div className="workout-detail-item">

                  <span>Intensity</span>

                  <strong>

                    {recommendation.intensity || "Not specified"}

                  </strong>

                </div>



                <div className="workout-detail-item">

                  <span>Workout type</span>

                  <strong>

                    {(recommendation.workout_type || "Run")

                      .replaceAll("_", " ")}

                  </strong>

                </div>



                <div className="workout-detail-item">

                  <span>Adaptation</span>

                  <strong>

                    {recommendation.adaptation || "Maintain"}

                  </strong>

                </div>

              </div>



              <div className="workout-coaching-note">

                <p className="eyebrow">YOUR COACH'S NOTE</p>

                <p>

                  {recommendation.adaptation_reason ||

                    recommendation.reason ||

                    "Follow a comfortable effort and listen to your body."}

                </p>

              </div>



              <div className="workout-modal-actions">

                <button

                  type="button"

                  className="workout-modal-done"

                  onClick={() => setShowWorkoutDetails(false)}

                >

                  Got it

                </button>

              </div>

            </section>

          </div>

        )}

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