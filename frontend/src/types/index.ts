// ─── Auth ────────────────────────────────────────────────────────────────────

export interface User {
  id: string
  username: string
  email: string
  is_admin: boolean
  is_active: boolean
  prize_points: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// ─── Series ───────────────────────────────────────────────────────────────────

export interface Series {
  id: string
  name: string
  cricapi_series_id: string | null
  status: string
  start_date: string | null
  end_date: string | null
  prize_pool: string
}

export interface SeriesCreate {
  name: string
  cricapi_series_id?: string
  status?: string
  start_date?: string
  end_date?: string
  prize_pool?: string
}

export interface SeriesPatch {
  name?: string
  cricapi_series_id?: string
  status?: string
  start_date?: string
  end_date?: string
  prize_pool?: string
}

// ─── Matches ──────────────────────────────────────────────────────────────────

export interface Match {
  id: string
  series_id: string
  cricapi_match_id: string | null
  name: string
  team_a: string
  team_b: string
  scheduled_at: string | null
  lock_time: string | null
  status: string
  prize_pool: string
  scorecard_updated_at: string | null
}

export interface MatchCreate {
  series_id: string
  name: string
  team_a: string
  team_b: string
  cricapi_match_id?: string
  scheduled_at?: string
  lock_time?: string
  prize_pool?: string
}

export interface MatchPatch {
  name?: string
  team_a?: string
  team_b?: string
  cricapi_match_id?: string
  scheduled_at?: string
  lock_time?: string
  status?: string
  prize_pool?: string
}

// ─── Players ──────────────────────────────────────────────────────────────────

export interface Player {
  id: string
  cricapi_player_id: string
  name: string
  role: string
  ipl_team: string | null
}

export interface MatchPlayer {
  player_id: string
  match_id: string
  team_name: string
  credit_value: string
  is_playing: boolean
  player: Player
}

// ─── Teams ────────────────────────────────────────────────────────────────────

export interface TeamPlayerDetail {
  player_id: string
  name: string
  role: string
  ipl_team: string | null
  credit_value: string
  team_name: string
  is_captain: boolean
  is_vice_captain: boolean
  points_earned: string
  multiplier: string
  final_points: string
}

export interface Team {
  id: string
  user_id: string
  match_id: string
  captain_id: string
  vice_captain_id: string
  total_points: string
  rank: number | null
  prize_awarded: string
  is_locked: boolean
  players: TeamPlayerDetail[]
}

export interface TeamCreate {
  player_ids: string[]
  captain_id: string
  vice_captain_id: string
}

// ─── Leaderboard ──────────────────────────────────────────────────────────────

export interface LeaderboardEntry {
  rank: number
  user_id: string
  username: string
  total_points: string
  prize_awarded: string
  captain_name: string
  vice_captain_name: string
}

export interface SeriesLeaderboardEntry {
  rank: number
  user_id: string
  username: string
  fantasy_points: string
  prize_awarded: string
  matches_played: number
}

export interface UserMatchHistory {
  match_id: string
  match_name: string
  scheduled_at: string | null
  match_status: string
  total_points: string
  rank: number | null
  prize_awarded: string
  captain_name: string
  vice_captain_name: string
}

// ─── Rules ────────────────────────────────────────────────────────────────────

export interface PointRule {
  id: string
  event_key: string
  role_filter: string | null
  points: string
}

export interface SelectionRule {
  id: string
  constraint_key: string
  value_int: number | null
  value_decimal: string | null
}

export interface RuleSet {
  id: string
  name: string
  description: string | null
  is_active: boolean
  point_rules: PointRule[]
  selection_rules: SelectionRule[]
}

// ─── Scoring ──────────────────────────────────────────────────────────────────

export interface PlayerScore {
  player_id: string
  player_name: string
  role: string
  runs: number
  fours: number
  sixes: number
  wickets: number
  maiden_overs: number
  catches: number
  stumpings: number
  run_outs: number
  raw_points: string
  override_points: string | null
  effective_points: string
}
