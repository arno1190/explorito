// User types
export interface UserProfile {
  id: string;
  display_name: string;
  avatar_url?: string;
  date_of_birth?: string;
  is_child: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  role: "admin" | "parent" | "child";
  is_active: boolean;
  created_at: string;
  profile?: UserProfile;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
  role?: "parent" | "child";
  date_of_birth?: string;
  parent_email?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Child types
export interface Child {
  id: string;
  name: string;
  birth_date: string;
  parent_id: string;
  created_at: string;
}

export interface CreateChildRequest {
  name: string;
  birth_date: string;
  email: string;
  password: string;
}

// Activity types
export interface Activity {
  id: string;
  title: string;
  description: string;
  category: string;
  min_age_months: number;
  max_age_months: number;
  duration_minutes: number;
  materials: string[];
  instructions: string[];
  created_at: string;
}

// API Error types
export interface ApiError {
  detail: string;
}

// Subject types
export interface Subject {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
  color: string;
  order_index: number;
  is_active: boolean;
  lesson_count: number;
}

// Lesson types
export interface Lesson {
  id: string;
  path_id: string; // Learning path ID
  subject_id?: string; // Subject ID (from learning path)
  name: string; // Changed from title to match backend
  description: string;
  order_index: number; // Changed from order to match backend
  unlock_criteria: Record<string, unknown>;
  xp_reward: number;
  estimated_duration: number | null;
  cover_image: string | null;
  is_published: boolean;
}

// Exercise types (both backend and frontend naming conventions)
export type ExerciseType =
  | "multiple_choice" // Frontend name
  | "mcq" // Backend name
  | "drag_and_drop" // Frontend name
  | "drag_drop" // Backend name
  | "fill_blanks"
  | "true_false"
  | "image_selection";

export interface Exercise {
  id: string;
  lesson_id: string;
  question: string;
  type: ExerciseType;
  content: ExerciseContent;
  correct_answer: Record<string, unknown>; // Backend sends this at exercise level
  order_index: number;
  difficulty: "easy" | "medium" | "hard";
  hints: Array<{ text: string; delay: number }>;
  explanation: string | null;
  media_urls: Record<string, string>;
  // Frontend compatibility - backend doesn't have these
  title?: string; // Use question as fallback
  points?: number; // Use 10 as default
  order?: number; // Use order_index as fallback
  created_at?: string;
}

export interface ExerciseContent {
  // Multiple Choice (frontend format)
  options?:
    | string[]
    | Array<{ id: string; text: string; image?: string | null }>;
  correct_answer?:
    | string
    | number
    | boolean
    | { answer: string }
    | { option_id: string };
  // Allow multiple selections for MCQ
  allowMultiple?: boolean;
  multiple?: boolean;
  // Keep original options for answer matching
  _originalOptions?: Array<{ id: string; text: string; image?: string | null }>;

  // Drag and Drop
  items?: Array<{ id: string; text: string }>;
  targets?: Array<{ id: string; text: string }>;
  correct_matches?: Record<string, string>;

  // Fill Blanks (frontend format)
  text?: string;
  blanks?: Array<{ position: number; answer: string }>;
  // Fill Blanks (backend format)
  sentence?: string;

  // Image Selection
  images?: Array<{ id: string; url: string; alt: string }>;
  correct_image_id?: string;

  // True/False
  statement?: string;

  // Generic image field (used by multiple types)
  image?: string | null;
}

export interface ExerciseSubmission {
  exercise_id: string;
  child_id: string;
  answer: unknown;
  is_correct: boolean;
  points_earned: number;
  time_spent_seconds: number;
}

export interface ExerciseResult {
  id: string;
  exercise_id: string;
  user_id: string;
  answer: Record<string, unknown>;
  is_correct: boolean;
  time_taken: number | null;
  hints_used: number;
  timestamp: string;
  // Frontend-added fields for display
  points_earned?: number;
  xp_gained?: number;
  feedback?: string;
  correct_answer?: unknown;
}

// Progress types
export interface Progress {
  id: string;
  child_id: string;
  lesson_id: string;
  exercises_completed: number;
  exercises_total: number;
  score: number;
  last_activity: string;
  created_at: string;
}

// Gamification types
export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  requirement: string;
  points: number;
  created_at: string;
}

export interface UserAchievement {
  id: string;
  child_id: string;
  achievement_id: string;
  earned_at: string;
  achievement: Achievement;
}

export interface GamificationStats {
  child_id: string;
  total_xp: number;
  level: number;
  current_level_xp: number;
  next_level_xp: number;
  current_streak: number;
  longest_streak: number;
  total_exercises_completed: number;
  achievements: UserAchievement[];
}
