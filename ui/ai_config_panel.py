"""AI Config Panel: Giao dien tuy chinh AI cho nguoi dung.

Cho phep:
- Chinh sua prompt templates
- Thay doi muc tieu/objectives cua AI
- Dieu chinh tham so model (temperature, top_p, max_tokens)
- Chon model uu tien
- Luu/load profiles cau hinh
- Bat/tat cac ky thuat AI
- Xem thong ke Vector Database
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json


class AIConfigPanel(ttk.Frame):
    """Panel tuy chinh cau hinh AI."""

    def __init__(self, parent, ai_config, vector_db=None):
        super().__init__(parent, padding=5)
        self.ai_config = ai_config
        self.vector_db = vector_db
        self._build_ui()

    def _build_ui(self):
        # Main notebook with sub-tabs
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Sub-tab 1: Prompt Templates
        self.prompts_frame = ttk.Frame(nb, padding=5)
        nb.add(self.prompts_frame, text=" Prompt Templates ")
        self._build_prompts_tab()

        # Sub-tab 2: Objectives
        self.obj_frame = ttk.Frame(nb, padding=5)
        nb.add(self.obj_frame, text=" Muc tieu AI ")
        self._build_objectives_tab()

        # Sub-tab 3: Model Parameters
        self.params_frame = ttk.Frame(nb, padding=5)
        nb.add(self.params_frame, text=" Tham so Model ")
        self._build_params_tab()

        # Sub-tab 4: Features & Vector DB
        self.features_frame = ttk.Frame(nb, padding=5)
        nb.add(self.features_frame, text=" Tinh nang & VectorDB ")
        self._build_features_tab()

        # Sub-tab 5: Profiles
        self.profiles_frame = ttk.Frame(nb, padding=5)
        nb.add(self.profiles_frame, text=" Profiles ")
        self._build_profiles_tab()

    # ==================================================================
    # Sub-tab 1: Prompt Templates
    # ==================================================================

    def _build_prompts_tab(self):
        f = self.prompts_frame

        ttk.Label(f, text="Chon prompt de chinh sua:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 3))

        # Prompt selector
        sel_row = ttk.Frame(f)
        sel_row.pack(fill="x", pady=3)

        self.prompt_key_var = tk.StringVar()
        descriptions = self.ai_config.get_prompt_descriptions()
        self.prompt_keys = list(descriptions.keys())
        prompt_display = [f"{k}: {v}" for k, v in descriptions.items()]

        self.prompt_combo = ttk.Combobox(
            sel_row, textvariable=self.prompt_key_var,
            values=prompt_display, state="readonly", width=65
        )
        self.prompt_combo.pack(side="left", padx=(0, 5))
        self.prompt_combo.bind("<<ComboboxSelected>>", self._on_prompt_selected)

        ttk.Button(sel_row, text="Reset", command=self._reset_prompt,
                   width=8).pack(side="right")

        # Prompt editor
        ttk.Label(f, text="Noi dung prompt:").pack(anchor="w", pady=(5, 2))
        self.prompt_text = scrolledtext.ScrolledText(
            f, height=10, font=("Consolas", 10), wrap="word"
        )
        self.prompt_text.pack(fill="both", expand=True, pady=3)

        # Buttons
        btn_row = ttk.Frame(f)
        btn_row.pack(fill="x", pady=3)
        ttk.Button(btn_row, text="LUU PROMPT", command=self._save_prompt).pack(side="left", padx=3)
        ttk.Button(btn_row, text="Reset tat ca", command=self._reset_all_prompts).pack(side="left", padx=3)

        # Select first prompt
        if prompt_display:
            self.prompt_combo.current(0)
            self._on_prompt_selected()

    def _on_prompt_selected(self, event=None):
        idx = self.prompt_combo.current()
        if idx < 0 or idx >= len(self.prompt_keys):
            return
        key = self.prompt_keys[idx]
        value = self.ai_config.get_prompt(key)
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", value)

    def _save_prompt(self):
        idx = self.prompt_combo.current()
        if idx < 0:
            return
        key = self.prompt_keys[idx]
        value = self.prompt_text.get("1.0", "end").strip()
        self.ai_config.set_prompt(key, value)
        self.ai_config.save()
        messagebox.showinfo("OK", f"Da luu prompt '{key}'.")

    def _reset_prompt(self):
        idx = self.prompt_combo.current()
        if idx < 0:
            return
        key = self.prompt_keys[idx]
        if messagebox.askyesno("Xac nhan", f"Reset prompt '{key}' ve mac dinh?"):
            self.ai_config.reset_prompt(key)
            self._on_prompt_selected()
            self.ai_config.save()

    def _reset_all_prompts(self):
        if messagebox.askyesno("Xac nhan", "Reset TAT CA prompts ve mac dinh?"):
            self.ai_config.reset_all_prompts()
            self._on_prompt_selected()
            self.ai_config.save()
            messagebox.showinfo("OK", "Da reset tat ca prompts.")

    # ==================================================================
    # Sub-tab 2: Objectives
    # ==================================================================

    def _build_objectives_tab(self):
        f = self.obj_frame

        ttk.Label(f, text="Muc tieu AI (objectives) - Dinh nghia AI tap trung vao dieu gi:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        # Objectives list
        list_frame = ttk.Frame(f)
        list_frame.pack(fill="both", expand=True, pady=3)

        self.obj_tree = ttk.Treeview(
            list_frame, columns=("Key", "Value"), show="headings", height=6
        )
        self.obj_tree.heading("Key", text="Ten muc tieu")
        self.obj_tree.heading("Value", text="Mo ta")
        self.obj_tree.column("Key", width=150)
        self.obj_tree.column("Value", width=450)
        self.obj_tree.pack(fill="both", expand=True, side="left")

        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.obj_tree.yview)
        sb.pack(side="right", fill="y")
        self.obj_tree.configure(yscrollcommand=sb.set)

        # Editor
        edit_frame = ttk.LabelFrame(f, text="Them/Sua muc tieu", padding=5)
        edit_frame.pack(fill="x", pady=5)

        row1 = ttk.Frame(edit_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Ten:").pack(side="left")
        self.obj_key_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.obj_key_var, width=20).pack(side="left", padx=5)

        ttk.Label(row1, text="Mo ta:").pack(side="left", padx=(10, 0))
        self.obj_val_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.obj_val_var, width=45).pack(side="left", padx=5)

        btn_row = ttk.Frame(edit_frame)
        btn_row.pack(fill="x", pady=3)
        ttk.Button(btn_row, text="Them/Cap nhat", command=self._add_objective).pack(side="left", padx=3)
        ttk.Button(btn_row, text="Xoa", command=self._delete_objective).pack(side="left", padx=3)
        ttk.Button(btn_row, text="LUU", command=self._save_objectives).pack(side="left", padx=3)

        self.obj_tree.bind("<<TreeviewSelect>>", self._on_obj_selected)
        self._refresh_objectives()

    def _refresh_objectives(self):
        for child in self.obj_tree.get_children():
            self.obj_tree.delete(child)
        for k, v in self.ai_config.get_objectives().items():
            self.obj_tree.insert("", "end", values=(k, v))

    def _on_obj_selected(self, event=None):
        sel = self.obj_tree.selection()
        if sel:
            vals = self.obj_tree.item(sel[0], "values")
            self.obj_key_var.set(vals[0])
            self.obj_val_var.set(vals[1])

    def _add_objective(self):
        key = self.obj_key_var.get().strip()
        val = self.obj_val_var.get().strip()
        if not key or not val:
            messagebox.showwarning("Chu y", "Nhap ten va mo ta muc tieu.")
            return
        self.ai_config.set_objective(key, val)
        self._refresh_objectives()

    def _delete_objective(self):
        key = self.obj_key_var.get().strip()
        if key:
            self.ai_config.remove_objective(key)
            self._refresh_objectives()
            self.obj_key_var.set("")
            self.obj_val_var.set("")

    def _save_objectives(self):
        self.ai_config.save()
        messagebox.showinfo("OK", "Da luu muc tieu AI.")

    # ==================================================================
    # Sub-tab 3: Model Parameters
    # ==================================================================

    def _build_params_tab(self):
        f = self.params_frame

        ttk.Label(f, text="Tham so Model AI:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        params = self.ai_config.get_model_params()

        # Temperature
        row1 = ttk.Frame(f)
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="Temperature (0.0 - 2.0):").pack(side="left")
        self.temp_var = tk.DoubleVar(value=params.get("temperature", 0.7))
        self.temp_scale = ttk.Scale(
            row1, from_=0.0, to=2.0, variable=self.temp_var,
            orient="horizontal", length=200
        )
        self.temp_scale.pack(side="left", padx=5)
        self.temp_label = ttk.Label(row1, text=f"{self.temp_var.get():.2f}", width=6)
        self.temp_label.pack(side="left")
        self.temp_var.trace_add("write", lambda *a: self.temp_label.configure(
            text=f"{self.temp_var.get():.2f}"))

        # Top P
        row2 = ttk.Frame(f)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Top P (0.0 - 1.0):       ").pack(side="left")
        self.top_p_var = tk.DoubleVar(value=params.get("top_p", 0.95))
        self.top_p_scale = ttk.Scale(
            row2, from_=0.0, to=1.0, variable=self.top_p_var,
            orient="horizontal", length=200
        )
        self.top_p_scale.pack(side="left", padx=5)
        self.top_p_label = ttk.Label(row2, text=f"{self.top_p_var.get():.2f}", width=6)
        self.top_p_label.pack(side="left")
        self.top_p_var.trace_add("write", lambda *a: self.top_p_label.configure(
            text=f"{self.top_p_var.get():.2f}"))

        # Max output tokens
        row3 = ttk.Frame(f)
        row3.pack(fill="x", pady=3)
        ttk.Label(row3, text="Max Output Tokens:       ").pack(side="left")
        self.max_tokens_var = tk.IntVar(value=params.get("max_output_tokens", 8192))
        ttk.Entry(row3, textvariable=self.max_tokens_var, width=10).pack(side="left", padx=5)

        # Model priority
        ttk.Label(f, text="\nThu tu model uu tien (moi dong 1 model):",
                  font=("", 10, "bold")).pack(anchor="w", pady=(5, 2))

        self.models_text = scrolledtext.ScrolledText(f, height=4, font=("Consolas", 10))
        self.models_text.pack(fill="x", pady=3)
        models = params.get("model_priority", [])
        self.models_text.insert("1.0", "\n".join(models))

        # Save button
        btn_row = ttk.Frame(f)
        btn_row.pack(fill="x", pady=5)
        ttk.Button(btn_row, text="LUU THAM SO", command=self._save_params).pack(side="left", padx=3)
        ttk.Button(btn_row, text="Reset mac dinh", command=self._reset_params).pack(side="left", padx=3)

    def _save_params(self):
        self.ai_config.set_model_param("temperature", round(self.temp_var.get(), 2))
        self.ai_config.set_model_param("top_p", round(self.top_p_var.get(), 2))
        self.ai_config.set_model_param("max_output_tokens", self.max_tokens_var.get())

        models_str = self.models_text.get("1.0", "end").strip()
        models = [m.strip() for m in models_str.split("\n") if m.strip()]
        if models:
            self.ai_config.set_model_priority(models)

        self.ai_config.save()
        messagebox.showinfo("OK", "Da luu tham so model.")

    def _reset_params(self):
        from core.ai_config import DEFAULT_MODEL_PARAMS
        if messagebox.askyesno("Xac nhan", "Reset tham so model ve mac dinh?"):
            for k, v in DEFAULT_MODEL_PARAMS.items():
                self.ai_config.set_model_param(k, v)
            self.temp_var.set(DEFAULT_MODEL_PARAMS["temperature"])
            self.top_p_var.set(DEFAULT_MODEL_PARAMS["top_p"])
            self.max_tokens_var.set(DEFAULT_MODEL_PARAMS["max_output_tokens"])
            self.models_text.delete("1.0", "end")
            self.models_text.insert("1.0", "\n".join(DEFAULT_MODEL_PARAMS["model_priority"]))
            self.ai_config.save()

    # ==================================================================
    # Sub-tab 4: Features & Vector DB
    # ==================================================================

    def _build_features_tab(self):
        f = self.features_frame

        # Features toggles
        ttk.Label(f, text="Bat/Tat tinh nang AI:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        features = self.ai_config.get_features()
        feature_labels = {
            "semantic_search": "Semantic Search (tim kiem ngu nghia)",
            "rag_enabled": "RAG (Retrieval Augmented Generation)",
            "multi_stage_pipeline": "Multi-stage Pipeline (nhieu buoc AI)",
            "pre_filter_locators": "Pre-filter Locators (loc truoc khi gui AI)",
            "semantic_chunking": "Semantic Chunking (chia nho use case)",
            "adaptive_processing": "Adaptive Processing (tu dong chon strategy)",
            "auto_heal_enabled": "Auto-Heal Locators (tu sua locator loi)",
            "vector_db_enabled": "Vector Database (luu embeddings)",
        }

        self.feature_vars = {}
        for feat, label in feature_labels.items():
            var = tk.BooleanVar(value=features.get(feat, False))
            self.feature_vars[feat] = var
            ttk.Checkbutton(f, text=label, variable=var).pack(anchor="w", pady=1)

        ttk.Button(f, text="LUU TINH NANG", command=self._save_features).pack(
            anchor="w", pady=5)

        # Vector DB stats
        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(f, text="Vector Database Info:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 3))

        self.vdb_info = scrolledtext.ScrolledText(
            f, height=8, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", state="disabled"
        )
        self.vdb_info.pack(fill="both", expand=True, pady=3)

        vdb_btn_row = ttk.Frame(f)
        vdb_btn_row.pack(fill="x", pady=3)
        ttk.Button(vdb_btn_row, text="Lam moi", command=self._refresh_vdb_info).pack(side="left", padx=3)
        ttk.Button(vdb_btn_row, text="Reindex", command=self._reindex_vdb).pack(side="left", padx=3)

        self._refresh_vdb_info()

    def _save_features(self):
        for feat, var in self.feature_vars.items():
            self.ai_config.set_feature(feat, var.get())
        self.ai_config.save()
        messagebox.showinfo("OK", "Da luu cau hinh tinh nang.")

    def _refresh_vdb_info(self):
        self.vdb_info.configure(state="normal")
        self.vdb_info.delete("1.0", "end")

        if self.vector_db:
            stats = self.vector_db.get_stats()
            info_lines = [
                f"Backend: {stats.get('backend', 'N/A')}",
                f"Embedding Model: {stats.get('embedding_model', 'N/A')}",
                f"Initialized: {stats.get('initialized', False)}",
                f"Semantic Search: {'Co' if self.vector_db.has_semantic_search else 'Hash-based'}",
                "",
                "Collections:",
            ]
            for name, count in stats.get("collections", {}).items():
                info_lines.append(f"  - {name}: {count} documents")
            self.vdb_info.insert("1.0", "\n".join(info_lines))
        else:
            self.vdb_info.insert("1.0", "Vector Database chua duoc khoi tao.\n"
                                        "Chon project path va cau hinh API key de bat dau.")

        self.vdb_info.configure(state="disabled")

    def _reindex_vdb(self):
        if not self.vector_db:
            messagebox.showwarning("Chu y", "Vector Database chua duoc khoi tao.")
            return
        if messagebox.askyesno("Xac nhan", "Xoa va index lai tat ca du lieu trong Vector DB?"):
            self.vector_db.reindex()
            self._refresh_vdb_info()
            messagebox.showinfo("OK", "Da reindex Vector Database.")

    # ==================================================================
    # Sub-tab 5: Profiles
    # ==================================================================

    def _build_profiles_tab(self):
        f = self.profiles_frame

        ttk.Label(f, text="Quan ly profiles cau hinh AI:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        # Current profile
        row1 = ttk.Frame(f)
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="Profile hien tai:").pack(side="left")
        self.profile_label = ttk.Label(
            row1, text=self.ai_config.get_active_profile(),
            foreground="blue", font=("", 10, "bold")
        )
        self.profile_label.pack(side="left", padx=5)

        # Profile list
        row2 = ttk.Frame(f)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Chon profile:").pack(side="left")
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            row2, textvariable=self.profile_var, state="readonly", width=25
        )
        self.profile_combo.pack(side="left", padx=5)
        ttk.Button(row2, text="Load", command=self._load_profile).pack(side="left", padx=3)
        ttk.Button(row2, text="Xoa", command=self._delete_profile).pack(side="left", padx=3)
        self._refresh_profiles()

        # Save new profile
        row3 = ttk.Frame(f)
        row3.pack(fill="x", pady=5)
        ttk.Label(row3, text="Luu profile moi:").pack(side="left")
        self.new_profile_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.new_profile_var, width=20).pack(side="left", padx=5)
        ttk.Button(row3, text="LUU", command=self._save_profile).pack(side="left", padx=3)

        # Export / Import
        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(f, text="Export/Import cau hinh:",
                  font=("", 10, "bold")).pack(anchor="w", pady=(0, 3))

        self.export_text = scrolledtext.ScrolledText(
            f, height=10, font=("Consolas", 9)
        )
        self.export_text.pack(fill="both", expand=True, pady=3)

        exp_row = ttk.Frame(f)
        exp_row.pack(fill="x", pady=3)
        ttk.Button(exp_row, text="Export", command=self._export_config).pack(side="left", padx=3)
        ttk.Button(exp_row, text="Import", command=self._import_config).pack(side="left", padx=3)

    def _refresh_profiles(self):
        profiles = self.ai_config.list_profiles()
        self.profile_combo["values"] = profiles
        if profiles:
            active = self.ai_config.get_active_profile()
            if active in profiles:
                self.profile_combo.current(profiles.index(active))
            else:
                self.profile_combo.current(0)

    def _load_profile(self):
        name = self.profile_var.get()
        if not name:
            return
        if self.ai_config.load_profile(name):
            self.profile_label.configure(text=name)
            self.ai_config.save()
            messagebox.showinfo("OK", f"Da load profile: {name}")
        else:
            messagebox.showwarning("Loi", f"Khong tim thay profile: {name}")

    def _save_profile(self):
        name = self.new_profile_var.get().strip()
        if not name:
            messagebox.showwarning("Chu y", "Nhap ten profile.")
            return
        self.ai_config.save_profile(name)
        self.ai_config.save()
        self.profile_label.configure(text=name)
        self._refresh_profiles()
        messagebox.showinfo("OK", f"Da luu profile: {name}")

    def _delete_profile(self):
        name = self.profile_var.get()
        if not name or name == "default":
            messagebox.showwarning("Chu y", "Khong the xoa profile 'default'.")
            return
        if messagebox.askyesno("Xac nhan", f"Xoa profile '{name}'?"):
            self.ai_config.delete_profile(name)
            self.ai_config.save()
            self._refresh_profiles()

    def _export_config(self):
        self.export_text.delete("1.0", "end")
        self.export_text.insert("1.0", self.ai_config.export_config())

    def _import_config(self):
        json_str = self.export_text.get("1.0", "end").strip()
        if not json_str:
            messagebox.showwarning("Chu y", "Dan JSON cau hinh vao o tren.")
            return
        if self.ai_config.import_config(json_str):
            self.ai_config.save()
            messagebox.showinfo("OK", "Da import cau hinh thanh cong.")
            self._refresh_profiles()
        else:
            messagebox.showerror("Loi", "JSON khong hop le.")

    # ------------------------------------------------------------------
    # Public method to update references
    # ------------------------------------------------------------------

    def set_vector_db(self, vector_db):
        """Cap nhat VectorDB reference."""
        self.vector_db = vector_db
        self._refresh_vdb_info()
