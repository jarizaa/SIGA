import os
import re
import docx


class RubricSIGAEvaluatorAgent:

    def __init__(self, docx_path):
        self.docx_path = docx_path
        self.text_content = ""
        self.raw_text_lower = ""
        self.desglose = {}
        self.puntos_fuertes = []
        self.areas_mejora = []
        self.fallos_criticos = []

        self._load_document()

    def _load_document(self):
        if not os.path.exists(self.docx_path):
            raise FileNotFoundError(
                f"No se encontró el archivo: {self.docx_path}"
            )

        doc = docx.Document(self.docx_path)
        full_text = []

        for p in doc.paragraphs:
            full_text.append(p.text)

        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    full_text.append(cell.text)

        self.text_content = "\n".join(full_text)
        self.raw_text_lower = self.text_content.lower()

    def _has_actual_code(self, keyword, min_length_after=20):
        """Busca de forma iterativa ocurrencias evitando falsos positivos en índices."""
        kw_lower = keyword.lower()
        pos = 0
        while True:
            pos = self.raw_text_lower.find(kw_lower, pos)
            if pos == -1:
                return False

            sub_text = self.text_content[
                pos + len(keyword):
                pos + len(keyword) + 180
            ].strip()

            if len(sub_text) >= min_length_after and not sub_text.startswith("..."):
                return True

            pos += len(keyword)

    def evaluate_linux(self):
        """Criterio 1: Sistema Linux/Oracle (15% -> 1.5 Pts)"""
        nota = 1.5
        detalles = []

        has_oracle_user = "oracle" in self.raw_text_lower or "siga_app" in self.raw_text_lower
        if not has_oracle_user:
            nota -= 0.5
            self.fallos_criticos.append("Linux: Ausencia total de usuarios de servicio (oracle/siga_app). [-0.5 pts]")
            detalles.append("Usuarios Linux (oracle/siga_app): FALTANTE (-0.5 pts)")
        else:
            detalles.append("Usuarios Linux: Correcto (0.0)")

        has_listener = "1521" in self.text_content or "firewall-cmd" in self.raw_text_lower
        if not has_listener:
            nota -= 0.4
            self.fallos_criticos.append("Linux: Falta configuración de red o puerto Listener 1521. [-0.4 pts]")
            detalles.append("Listener 1521 / Red: FALTANTE (-0.4 pts)")
        else:
            detalles.append("Listener 1521 / Red: Correcto (0.0)")

        has_ts = "create tablespace" in self.raw_text_lower and "siga_data" in self.raw_text_lower
        if not has_ts:
            nota -= 0.3
            self.fallos_criticos.append("Linux/Oracle: Falta la creación del tablespace 'siga_data'. [-0.3 pts]")
            detalles.append("Tablespace 'siga_data': FALTANTE (-0.3 pts)")
        else:
            detalles.append("Tablespace: Correcto (0.0)")

        has_backup = "expdp" in self.raw_text_lower or "data pump" in self.raw_text_lower or "cron" in self.raw_text_lower
        if not has_backup:
            nota -= 0.3
            self.areas_mejora.append("Linux: Sin estrategia documentada de backups con Data Pump o cron. [-0.3 pts]")
            detalles.append("Copias de seguridad Data Pump/cron: FALTANTE (-0.3 pts)")
        else:
            detalles.append("Copias de seguridad: Correcto (0.0)")

        if nota == 1.5:
            self.puntos_fuertes.append("Sistema Linux y Oracle correctamente configurados y documentados.")

        nota = max(0.0, round(nota, 2))
        self.desglose["1_Linux_Oracle"] = {"nota": nota, "max": 1.5, "detalles": detalles}

    def evaluate_db_design(self):
        """Criterio 2: Diseño y normalización de la base de datos (15% -> 1.5 Pts)"""
        nota = 1.5
        detalles = []

        has_seq = "create sequence" in self.raw_text_lower and self._has_actual_code("create sequence", 10)
        if not has_seq:
            nota -= 0.5
            self.fallos_criticos.append("Base de Datos: Faltan secuencias DDL de autoincremento (seq_*). [-0.5 pts]")
            detalles.append("Secuencias DDL: FALTANTE (-0.5 pts)")
        else:
            detalles.append("Secuencias DDL: Correcto (0.0)")

        tablas = ["categorias", "alumnos", "libros", "bibliotecarios", "prestamos"]
        tablas_faltantes = [
            t for t in tablas
            if f"create table {t}" not in self.raw_text_lower
            or not self._has_actual_code(f"create table {t}", 15)
        ]

        if tablas_faltantes:
            pen = min(1.0, len(tablas_faltantes) * 0.3)
            nota -= pen
            self.fallos_criticos.append(f"Base de Datos: Faltan tablas normalizadas en 3FN: {', '.join(tablas_faltantes)}. [-{pen:.1f} pts]")
            detalles.append(f"Tablas faltantes ({', '.join(tablas_faltantes)}): -{pen:.1f} pts")
        else:
            detalles.append("Normalización y Tablas 3FN: Correcto (0.0)")

        if nota == 1.5:
            self.puntos_fuertes.append("Diseño y normalización de base de datos correctos hasta 3FN.")

        nota = max(0.0, round(nota, 2))
        self.desglose["2_Diseno_BD"] = {"nota": nota, "max": 1.5, "detalles": detalles}

    def evaluate_sql_plsql(self):
        """Criterio 3: Calidad del SQL/PL-SQL (procedimientos, triggers, transacciones) (20% -> 2.0 Pts)"""
        nota = 2.0
        detalles = []

        trg1 = "trg_evita_doble_prestamo" in self.raw_text_lower and self._has_actual_code("trg_evita_doble_prestamo", 30)
        trg2 = "trg_marca_devolucion" in self.raw_text_lower and self._has_actual_code("trg_marca_devolucion", 30)
        if not (trg1 and trg2):
            nota -= 0.8
            self.fallos_criticos.append("PL/SQL: Faltan triggers de negocio obligatorios (trg_evita_doble_prestamo / trg_marca_devolucion). [-0.8 pts]")
            detalles.append("Triggers PL/SQL: FALTANTES / INCOMPLETOS (-0.8 pts)")
        else:
            detalles.append("Triggers PL/SQL: Correcto (0.0)")

        proc = "sp_prestamos_vencidos" in self.raw_text_lower and self._has_actual_code("sp_prestamos_vencidos", 30)
        func = "fn_prestamos_activos" in self.raw_text_lower and self._has_actual_code("fn_prestamos_activos", 20)
        if not (proc and func):
            nota -= 0.8
            self.fallos_criticos.append("PL/SQL: Faltan procedimientos (sp_prestamos_vencidos) o funciones (fn_prestamos_activos). [-0.8 pts]")
            detalles.append("Procedimiento o Función PL/SQL: FALTANTE (-0.8 pts)")
        elif not ("sys_refcursor" in self.raw_text_lower or "refcursor" in self.raw_text_lower):
            nota -= 0.3
            self.areas_mejora.append("PL/SQL: El procedimiento no implementa SYS_REFCURSOR. [-0.3 pts]")
            detalles.append("SYS_REFCURSOR: Ausente (-0.3 pts)")
        else:
            detalles.append("Procedimientos y Funciones PL/SQL: Correcto (0.0)")

        view = "vw_catalogo_disponible" in self.raw_text_lower and self._has_actual_code("vw_catalogo_disponible", 15)
        if not view:
            nota -= 0.4
            self.areas_mejora.append("SQL: Falta la vista de catálogo 'vw_catalogo_disponible'. [-0.4 pts]")
            detalles.append("Vista de catálogo SQL: Ausente (-0.4 pts)")
        else:
            detalles.append("Vistas y Consultas SQL: Correcto (0.0)")

        if nota == 2.0:
            self.puntos_fuertes.append("Alta calidad en scripts SQL y PL/SQL con triggers y cursores robustos.")

        nota = max(0.0, round(nota, 2))
        self.desglose["3_Calidad_SQL_PLSQL"] = {"nota": nota, "max": 2.0, "detalles": detalles}

    def evaluate_java_oo(self):
        """Criterio 4: Diseño orientado a objetos y calidad del código Java (20% -> 2.0 Pts)"""
        nota = 2.0
        detalles = []

        poo_elements = ["persona", "alumno", "bibliotecario", "prestable", "libro"]
        missing_poo = [e for e in poo_elements if e not in self.raw_text_lower]
        if missing_poo:
            nota -= 0.8
            self.fallos_criticos.append(f"Java POO: Faltan clases o interfaces de la jerarquía: {', '.join(missing_poo)}. [-0.8 pts]")
            detalles.append(f"Jerarquía POO incompleta ({', '.join(missing_poo)}): -0.8 pts")
        else:
            detalles.append("Diseño Orientado a Objetos (Herencia/Interfaces): Correcto (0.0)")

        props = "config.properties" in self.raw_text_lower and "getresourceasstream" in self.raw_text_lower
        if not props:
            nota -= 0.4
            self.fallos_criticos.append("Java: No se externalizan credenciales en config.properties con getResourceAsStream(). [-0.4 pts]")
            detalles.append("config.properties externo: FALTANTE (-0.4 pts)")
        else:
            detalles.append("config.properties externo: Correcto (0.0)")

        jdbc_safe = "preparedstatement" in self.raw_text_lower and "callablestatement" in self.raw_text_lower
        if not jdbc_safe:
            nota -= 0.4
            self.fallos_criticos.append("Java JDBC: No se evidencia el uso seguro de PreparedStatement / CallableStatement. [-0.4 pts]")
            detalles.append("JDBC Seguro (PreparedStatement): FALTANTE (-0.4 pts)")
        else:
            detalles.append("Persistencia JDBC Segura: Correcto (0.0)")

        ex = "libronodisponibleexception" in self.raw_text_lower and "autenticacionexception" in self.raw_text_lower
        if not ex:
            nota -= 0.4
            self.fallos_criticos.append("Java: Faltan excepciones de dominio personalizadas. [-0.4 pts]")
            detalles.append("Excepciones de dominio: FALTANTE (-0.4 pts)")
        else:
            detalles.append("Excepciones de dominio: Correcto (0.0)")

        if nota == 2.0:
            self.puntos_fuertes.append("Código Java estructurado bajo principios OO limpios y JDBC seguro.")

        nota = max(0.0, round(nota, 2))
        self.desglose["4_Java_OO"] = {"nota": nota, "max": 2.0, "detalles": detalles}

    def evaluate_web(self):
        """Criterio 5: Funcionamiento de la capa web (10% -> 1.0 Pt)"""
        nota = 1.0
        detalles = []

        servidor = "httpserver" in self.raw_text_lower or "servlet" in self.raw_text_lower
        if not servidor:
            nota -= 0.6
            self.fallos_criticos.append("Capa Web: Falta servidor HTTP embebido o servlets. [-0.6 pts]")
            detalles.append("Servidor HTTP / Servlets: FALTANTE (-0.6 pts)")
        else:
            detalles.append("Servidor HTTP / Servlets: Correcto (0.0)")

        frontend = "fetch(" in self.raw_text_lower or "catalogo.html" in self.raw_text_lower
        if not frontend:
            nota -= 0.4
            self.areas_mejora.append("Capa Web: Falta página HTML frontal con fetch(). [-0.4 pts]")
            detalles.append("Frontend HTML con fetch: Ausente (-0.4 pts)")
        else:
            detalles.append("Frontend HTML con fetch: Correcto (0.0)")

        if nota == 1.0:
            self.puntos_fuertes.append("Capa web operativa y conectada correctamente al backend.")

        nota = max(0.0, round(nota, 2))
        self.desglose["5_Capa_Web"] = {"nota": nota, "max": 1.0, "detalles": detalles}

    def evaluate_teamwork(self):
        """Criterio 6: Trabajo en equipo y reparto equilibrado de tareas (10% -> 1.0 Pt)"""
        nota = 1.0
        detalles = []

        team_keywords = ["equipo", "roles", "integrantes", "reparto", "participación", "tareas", "colaboración"]
        has_teamwork = any(kw in self.raw_text_lower for kw in team_keywords)
        
        if not has_teamwork:
            nota -= 0.5
            self.areas_mejora.append("Memoria: No se detalla el trabajo en equipo ni el reparto de tareas entre los integrantes. [-0.5 pts]")
            detalles.append("Reparto de tareas y roles: No especificado (-0.5 pts)")
        else:
            detalles.append("Trabajo en equipo y roles documentados: Correcto (0.0)")

        if nota == 1.0:
            self.puntos_fuertes.append("Correcta organización y reparto de tareas documentado en el equipo.")

        nota = max(0.0, round(nota, 2))
        self.desglose["6_Trabajo_Equipo"] = {"nota": nota, "max": 1.0, "detalles": detalles}

    def evaluate_memory(self):
        """Criterio 7: Memoria técnica y defensa oral (10% -> 1.0 Pt)"""
        nota = 1.0
        detalles = []

        if len(self.text_content) < 1000:
            nota -= 0.5
            self.fallos_criticos.append("Memoria: El documento técnico es demasiado breve o carece de desarrollo formal. [-0.5 pts]")
            detalles.append("Extensión y profundidad de la memoria: Insuficiente (-0.5 pts)")
        else:
            detalles.append("Estructura y calidad formal de la memoria: Correcto (0.0)")

        if nota == 1.0:
            self.puntos_fuertes.append("Memoria técnica detallada, formal y bien estructurada.")

        nota = max(0.0, round(nota, 2))
        self.desglose["7_Memoria_Tecnica"] = {"nota": nota, "max": 1.0, "detalles": detalles}

    def _generate_feedback(self):
        nota_total = sum(item["nota"] for item in self.desglose.values())

        if nota_total >= 9.0:
            return "Proyecto excelente. Cumple rigurosamente con todos los criterios de la rúbrica oficial."
        elif nota_total >= 7.0:
            return "Notable. Proyecto sólido y funcional, con leves carencias en apartados secundarios."
        elif nota_total >= 5.0:
            return "Aprobado (Apto). Se alcanzan los mínimos exigidos por la rúbrica, aunque existen áreas mejorables."
        return "Suspenso (No Apto). El proyecto no cumple los mínimos establecidos en la rúbrica de evaluación."

    def run_evaluation(self):
        self.evaluate_linux()
        self.evaluate_db_design()
        self.evaluate_sql_plsql()
        self.evaluate_java_oo()
        self.evaluate_web()
        self.evaluate_teamwork()
        self.evaluate_memory()

        nota_final = round(
            sum(modulo["nota"] for modulo in self.desglose.values()),
            2
        )
        resultado = "APTO" if nota_final >= 5.0 else "NO APTO"

        return {
            "calificacion_global": nota_final,
            "resultado": resultado,
            "feedback_alumno": self._generate_feedback(),
            "fallos_criticos": self.fallos_criticos,
            "desglose_modulos": self.desglose,
            "puntos_fuertes": self.puntos_fuertes,
            "areas_mejora": self.areas_mejora
        }