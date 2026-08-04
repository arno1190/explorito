"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  createChildApiV1ChildrenPost,
  deleteChildApiV1ChildrenChildIdDelete,
  getChildrenApiV1ChildrenGet,
  updateChildApiV1ChildrenChildIdPut,
} from "@/lib/api/generated/children/children";
import { getChildStatsApiV1GamificationChildIdStatsGet } from "@/lib/api/generated/gamification/gamification";
import type { LevelEnum } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UserAvatar } from "@/components/profile/UserAvatar";
import { AvatarPicker } from "@/components/profile/AvatarPicker";
import { PinDialog } from "@/components/profile/PinDialog";
import { uploadFile } from "@/lib/api/axios-instance";
import { Plus, Trash2, Play, TrendingUp } from "lucide-react";
import type { ChildResponse, ChildStatsResponse } from "@/lib/api/model";

const LEVELS: { value: LevelEnum; label: string }[] = [
  { value: "ps", label: "Petite Section" },
  { value: "ms", label: "Moyenne Section" },
  { value: "gs", label: "Grande Section" },
  { value: "cp", label: "CP" },
  { value: "ce1", label: "CE1" },
  { value: "ce2", label: "CE2" },
  { value: "cm1", label: "CM1" },
  { value: "cm2", label: "CM2" },
];

export default function DashboardPage() {
  const { user, impersonateChild } = useAuth();
  const router = useRouter();
  const [children, setChildren] = useState<ChildResponse[]>([]);
  const [childrenStats, setChildrenStats] = useState<
    Record<string, ChildStatsResponse>
  >({});
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [level, setLevel] = useState<LevelEnum>("cp");
  // Lancement du mode enfant : protégé par le code PIN parent. S'il n'existe pas
  // encore, on invite à le définir avant de basculer.
  const [pinOpen, setPinOpen] = useState(false);
  const [pendingChild, setPendingChild] = useState<ChildResponse | null>(null);

  const launchChild = (child: ChildResponse) => {
    if (user?.has_pin) {
      impersonateChild(child);
    } else {
      setPendingChild(child);
      setPinOpen(true);
    }
  };
  const [error, setError] = useState("");
  const [avatarChildId, setAvatarChildId] = useState<string | null>(null);

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    try {
      setLoading(true);
      const data = await getChildrenApiV1ChildrenGet();
      setChildren(data);

      // Load stats for each child
      const statsPromises = data.map(async (child) => {
        try {
          const stats = await getChildStatsApiV1GamificationChildIdStatsGet(
            child.id
          );
          return { id: child.id, stats };
        } catch (err) {
          console.error(`Failed to load stats for child ${child.id}:`, err);
          return { id: child.id, stats: null };
        }
      });

      const statsResults = await Promise.all(statsPromises);
      const statsMap: Record<string, ChildStatsResponse> = {};
      statsResults.forEach(({ id, stats }) => {
        if (stats) {
          statsMap[id] = stats;
        }
      });
      setChildrenStats(statsMap);
    } catch (err) {
      console.error("Failed to load children:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddChild = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await createChildApiV1ChildrenPost({
        name,
        birth_date: birthDate || undefined,
        level,
      });
      setDialogOpen(false);
      setName("");
      setBirthDate("");
      setLevel("cp");
      loadChildren();
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to add child. Please try again."
      );
    }
  };

  const handleDeleteChild = async (id: string) => {
    if (!confirm("Are you sure you want to delete this child?")) {
      return;
    }

    try {
      await deleteChildApiV1ChildrenChildIdDelete(id);
      loadChildren();
    } catch (err) {
      console.error("Failed to delete child:", err);
    }
  };

  const handleChangeLevel = async (id: string, newLevel: LevelEnum) => {
    // Optimistic UI, then persist.
    setChildren((prev) =>
      prev.map((c) => (c.id === id ? { ...c, level: newLevel } : c))
    );
    try {
      await updateChildApiV1ChildrenChildIdPut(id, { level: newLevel });
    } catch (err) {
      console.error("Failed to change level:", err);
      loadChildren(); // revert to server truth
    }
  };

  const handleChangeAvatar = async (id: string, avatar: string) => {
    setChildren((prev) =>
      prev.map((c) => (c.id === id ? { ...c, avatar_url: avatar } : c))
    );
    try {
      await updateChildApiV1ChildrenChildIdPut(id, { avatar_url: avatar });
    } catch (err) {
      console.error("Failed to change avatar:", err);
      loadChildren();
    }
  };

  const handleUploadChildAvatar = async (id: string, file: File) => {
    await uploadFile(`/api/v1/children/${id}/avatar`, file);
    loadChildren();
  };

  const calculateAge = (birthDate: string) => {
    const today = new Date();
    const birth = new Date(birthDate);
    const months = Math.floor(
      (today.getTime() - birth.getTime()) / (1000 * 60 * 60 * 24 * 30.44)
    );
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;

    if (years === 0) {
      return `${months} months`;
    }
    return `${years} year${years > 1 ? "s" : ""} ${remainingMonths} month${remainingMonths !== 1 ? "s" : ""}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Welcome, {user?.profile?.display_name || "User"}!
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage your children and discover age-appropriate activities
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Child
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={handleAddChild}>
              <DialogHeader>
                <DialogTitle>Add a new child</DialogTitle>
                <DialogDescription>
                  Add your child's information to get personalized activity
                  recommendations
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {error && (
                  <div className="bg-fun-red-light text-fun-red p-3 rounded-xl text-sm">
                    {error}
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="birthDate">
                    Date de naissance (optionnel)
                  </Label>
                  <Input
                    id="birthDate"
                    type="date"
                    value={birthDate}
                    onChange={(e) => setBirthDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="level">Niveau scolaire</Label>
                  <select
                    id="level"
                    value={level}
                    onChange={(e) => setLevel(e.target.value as LevelEnum)}
                    className="h-11 w-full rounded-xl border-2 border-fun-border bg-white px-3 text-fun-text outline-none focus:border-fun-sky"
                  >
                    {LEVELS.map((l) => (
                      <option key={l.value} value={l.value}>
                        {l.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Add Child</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
        </div>
      ) : children.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">
              You haven't added any children yet.
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add your first child
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {children.map((child) => {
            const stats = childrenStats[child.id];
            return (
              <Card key={child.id} className="overflow-hidden candy-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => setAvatarChildId(child.id)}
                        title="Changer l'avatar"
                        className="rounded-full ring-fun-green transition-all hover:ring-2 active:scale-95"
                      >
                        <UserAvatar
                          avatar={child.avatar_url}
                          name={child.name}
                          className="h-12 w-12"
                          textClassName="text-2xl"
                        />
                      </button>
                      <CardTitle className="text-xl">{child.name}</CardTitle>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteChild(child.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                  <AvatarPicker
                    open={avatarChildId === child.id}
                    onOpenChange={(o) => !o && setAvatarChildId(null)}
                    current={child.avatar_url}
                    onSelect={(a) => handleChangeAvatar(child.id, a)}
                    uploader={(f) => handleUploadChildAvatar(child.id, f)}
                    title={`Avatar de ${child.name}`}
                  />
                  <CardDescription>
                    {child.birth_date
                      ? `Âge : ${calculateAge(child.birth_date)}`
                      : "Âge non renseigné"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Niveau scolaire (modifiable par le parent) */}
                  <div className="flex items-center justify-between gap-2 rounded-xl bg-fun-sky-light px-3 py-2">
                    <span className="text-sm font-semibold text-fun-text">
                      Niveau
                    </span>
                    <select
                      value={child.level ?? ""}
                      onChange={(e) =>
                        handleChangeLevel(child.id, e.target.value as LevelEnum)
                      }
                      className="h-9 rounded-lg border-2 border-fun-border bg-white px-2 text-sm font-semibold text-fun-text outline-none focus:border-fun-sky"
                    >
                      {!child.level && <option value="">Choisir…</option>}
                      {LEVELS.map((l) => (
                        <option key={l.value} value={l.value}>
                          {l.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Stats Display */}
                  {stats && (
                    <div className="grid grid-cols-2 gap-2 py-3 px-2 bg-muted rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-fun-sun">
                          ⚡ {stats.total_xp}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          XP Total
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-fun-sun">
                          🔥 {stats.current_streak}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Jours
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Progress bar */}
                  {stats && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Niveau {stats.level}</span>
                        <span>
                          {stats.current_level_xp} / {stats.next_level_xp} XP
                        </span>
                      </div>
                      <div className="w-full bg-fun-green-light rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-fun-green to-fun-sky h-2 rounded-full transition-all"
                          style={{
                            width: `${(stats.current_level_xp / stats.next_level_xp) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="space-y-2 pt-2">
                    <Button
                      className="w-full"
                      onClick={() => launchChild(child)}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      Jouer comme {child.name}
                    </Button>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={() => router.push(`/progress/${child.id}`)}
                    >
                      <TrendingUp className="mr-2 h-4 w-4" />
                      Voir les progrès
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <PinDialog
        open={pinOpen}
        onOpenChange={setPinOpen}
        mode="set"
        onSuccess={() => {
          if (pendingChild) impersonateChild(pendingChild);
          setPendingChild(null);
        }}
      />
    </div>
  );
}
