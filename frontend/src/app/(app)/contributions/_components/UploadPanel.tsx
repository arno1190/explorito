"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ClipboardPaste, FileUp, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getListMyPacksApiV1ContributionsGetQueryKey } from "@/lib/api/generated/contributions/contributions";
import type { UploadResult } from "@/lib/api/model";

import {
  parseApiFailure,
  uploadFailureTitle,
  uploadPack,
  type ApiFailure,
} from "../_lib/contrib";
import { IssueList } from "./IssueList";

type Mode = "file" | "text";

/**
 * Dépôt d'un pack. Les conditions se prennent maintenant à l'arrivée sur la
 * page : ici, un 428 ne fait que renvoyer le parent vers ce même dialogue.
 */
export function UploadPanel({
  disabled = false,
  onTermsRequired,
}: {
  disabled?: boolean;
  onTermsRequired: () => void;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [mode, setMode] = useState<Mode>("file");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [failure, setFailure] = useState<ApiFailure | null>(null);

  const upload = useMutation({
    mutationFn: uploadPack,
    onSuccess: (result: UploadResult) => {
      setFailure(null);
      queryClient.invalidateQueries({
        queryKey: getListMyPacksApiV1ContributionsGetQueryKey(),
      });
      router.push(`/contributions/${result.pack_id}`);
    },
    onError: (error: unknown) => {
      const parsed = parseApiFailure(error);
      if (parsed.status === 428) {
        onTermsRequired();
        return;
      }
      setFailure(parsed);
    },
  });

  const submitCurrent = () => {
    if (disabled) return;
    setFailure(null);
    if (mode === "file") {
      if (!file) return;
      upload.mutate({ source: { kind: "file", file } });
      return;
    }
    try {
      JSON.parse(text);
    } catch {
      // Refus local : inutile de faire un aller-retour pour du JSON tronqué.
      setFailure({
        status: 400,
        code: null,
        message:
          "Le texte collé n'est pas du JSON valide. Recopiez tout le fichier, des premières accolades aux dernières.",
        issues: [],
      });
      return;
    }
    upload.mutate({ source: { kind: "text", text } });
  };

  const canSubmit = mode === "file" ? file !== null : text.trim().length > 0;

  return (
    <section className="rounded-2xl bg-white p-5 candy-shadow">
      <h2 className="flex items-center gap-2 text-xl font-extrabold text-fun-text">
        <Upload className="h-5 w-5 text-fun-green" />
        Déposer un pack
      </h2>
      <p className="mt-1 text-sm text-fun-text-muted">
        Envoyez le fichier <code className="font-mono">.explorito</code> écrit
        par votre assistant. Rien n&apos;est publié à cette étape : vous relisez
        d&apos;abord l&apos;aperçu, puis vous soumettez.
      </p>

      <div className="mt-4 flex gap-2">
        <Button
          type="button"
          variant={mode === "file" ? "default" : "outline"}
          onClick={() => setMode("file")}
        >
          <FileUp className="h-4 w-4" />
          Un fichier
        </Button>
        <Button
          type="button"
          variant={mode === "text" ? "default" : "outline"}
          onClick={() => setMode("text")}
        >
          <ClipboardPaste className="h-4 w-4" />
          Coller le JSON
        </Button>
      </div>

      <div className="mt-4">
        {mode === "file" ? (
          <label
            className={cn(
              "flex min-h-24 cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed p-6 text-center transition-all",
              file
                ? "border-fun-green bg-fun-green-light"
                : "border-fun-border bg-fun-card hover:border-fun-sky"
            )}
          >
            <input
              type="file"
              accept=".explorito,.json,application/json"
              className="sr-only"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setFailure(null);
              }}
            />
            <FileUp className="h-6 w-6 text-fun-green" />
            <span className="text-sm font-bold text-fun-text">
              {file ? file.name : "Choisir un fichier .explorito ou .json"}
            </span>
            {file && (
              <span className="text-xs text-fun-text-muted">
                {Math.round(file.size / 1024)} Ko
              </span>
            )}
          </label>
        ) : (
          <textarea
            value={text}
            onChange={(event) => {
              setText(event.target.value);
              setFailure(null);
            }}
            rows={8}
            spellCheck={false}
            placeholder={
              '{\n  "title": "Les dinosaures",\n  "lessons": [ … ]\n}'
            }
            className="w-full rounded-2xl border-2 border-fun-border bg-fun-card p-4 font-mono text-sm text-fun-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fun-sky"
          />
        )}
      </div>

      <Button
        className="mt-4 w-full sm:w-auto"
        size="lg"
        onClick={submitCurrent}
        disabled={disabled || !canSubmit || upload.isPending}
      >
        {upload.isPending ? "Envoi…" : "Envoyer le brouillon"}
      </Button>

      {failure && (
        <div className="mt-4 rounded-2xl border-2 border-fun-red bg-fun-red-light p-4">
          <p className="font-extrabold text-fun-text">
            {uploadFailureTitle(failure)}
          </p>
          <p className="mt-1 text-sm text-fun-text">{failure.message}</p>
          {failure.issues.length > 0 && (
            <>
              <p className="mt-3 text-sm font-semibold text-fun-text">
                Recopiez ces lignes à votre assistant : elles suffisent à
                corriger le fichier.
              </p>
              <IssueList className="mt-2" issues={failure.issues} />
            </>
          )}
          {failure.status === 413 && (
            <p className="mt-2 text-sm text-fun-text">
              Coupez le contenu en deux packs plus courts, ou retirez les images
              encodées dans le fichier.
            </p>
          )}
          {failure.status === 429 && (
            <p className="mt-2 text-sm text-fun-text">
              En attendant, vous pouvez continuer à corriger un brouillon déjà
              envoyé : les corrections ne comptent pas dans cette limite.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
