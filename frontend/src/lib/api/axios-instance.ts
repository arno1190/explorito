import axios, { AxiosError, AxiosRequestConfig } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

// NB: the Orval-generated client already includes the full `/api/v1/...` path,
// so the baseURL must be the bare host (no `/api/v1`) to avoid a double prefix.
const instance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
instance.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // En mode incarnation (parent « joue en tant que » un enfant), on indique
    // l'enfant actif au backend pour qu'il filtre/verrouille le contenu selon
    // SON niveau et SA progression, et non ceux du parent.
    const impersonated = localStorage.getItem("impersonated_child");
    if (impersonated) {
      try {
        const child = JSON.parse(impersonated);
        if (child?.id) config.headers["X-Acting-Child-Id"] = String(child.id);
      } catch {
        // ignore un JSON invalide
      }
    }
    // Mode admin « voir en tant que » : l'admin observe l'app dans la peau d'un
    // autre compte (parent ou enfant). Le backend applique alors les droits et
    // les données de ce compte cible.
    const impersonateUser = localStorage.getItem("impersonate_user");
    if (impersonateUser) {
      config.headers["X-Impersonate-User-Id"] = String(impersonateUser);
    }
  }
  // Pour un envoi multipart (upload), laisser axios définir le Content-Type
  // avec la bonne « boundary » plutôt que le JSON par défaut de l'instance.
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

// Response interceptor to handle errors
instance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // La vérification du PIN renvoie 401 en cas de code erroné : c'est une
    // erreur métier gérée par l'appelant, pas une session expirée -> ne pas
    // déconnecter ni rediriger.
    const url = error.config?.url ?? "";
    const isPinCheck = url.includes("/auth/verify-pin");
    if (error.response?.status === 401 && !isPinCheck) {
      // Clear token and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/** Upload d'un fichier (multipart) via l'instance authentifiée. */
export async function uploadFile<T = unknown>(
  url: string,
  file: File,
  field = "file"
): Promise<T> {
  const form = new FormData();
  form.append(field, file);
  const { data } = await instance.post<T>(url, form);
  return data;
}

// Custom instance for Orval - named export required
export const axiosInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  const source = axios.CancelToken.source();
  const promise = instance({
    ...config,
    cancelToken: source.token,
  }).then(({ data }) => data);

  // @ts-expect-error - Orval expects cancel property
  promise.cancel = () => {
    source.cancel("Query was cancelled");
  };

  return promise;
};

export default axiosInstance;
