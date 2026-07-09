from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from lxml import etree

from .schemas import CourseStructure


class MoodleXmlExporter:
    def export(
        self,
        course: CourseStructure,
        output_file: Path,
        ada_structure: dict[str, Any] | None = None,
        question_bank: list[dict[str, Any]] | None = None,
        question_bank_category: str = "Banco de preguntas",
    ) -> Path:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        root = etree.Element("quiz")

        if ada_structure:
            self._export_ada_centric(root, ada_structure)
        else:
            for module in course.modulos:
                self._add_category(root, module.titulo)

                for lesson in module.lecciones:
                    self._add_description_question(root, module.titulo, lesson.titulo, lesson.texto, lesson.image_path)
                    self._add_activity_question(root, module.titulo, lesson.titulo, lesson.actividad)

        if question_bank:
            self._add_category(root, question_bank_category)
            for item in question_bank:
                self._add_multichoice_question(root, item)

        tree = etree.ElementTree(root)
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)
        return output_file

    def export_quiz(
        self,
        items: list[dict[str, Any]],
        output_file: Path,
        category: str = "Quiz",
    ) -> Path:
        """Exporta un XML de banco de preguntas de Moodle solo con los reactivos del
        quiz, bajo una categoria propia. En Moodle se importa y se construye el Quiz
        seleccionando esta categoria."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        root = etree.Element("quiz")
        self._add_category(root, category)
        for item in items:
            self._add_multichoice_question(root, item)

        tree = etree.ElementTree(root)
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)
        return output_file

    def _export_ada_centric(self, root: etree._Element, ada_structure: dict[str, Any]) -> None:
        """Construye el banco de preguntas con una sección por ADA: páginas de
        contenido (sesiones), lecturas por eje tematico y un unico entregable."""
        periodos = ada_structure.get("periodos") or []
        for periodo in periodos:
            adas: list[dict[str, Any]] = list(periodo.get("adas") or [])
            fase = periodo.get("fase_proyecto_integrador") or {}
            integradora = fase.get("ada_integradora_producto")
            if integradora:
                adas.append(integradora)

            for ada in adas:
                ada_name = ada.get("nombre", "ADA")
                self._add_category(root, ada_name)

                for sesion in ada.get("sesiones_desarrolladas") or []:
                    self._add_session_page(root, ada_name, sesion)

                self._add_presentation_page(root, ada_name, ada)

                for reading in ada.get("lecturas_fundamentacion") or []:
                    self._add_reading_question(root, ada_name, reading)

                self._add_ada_deliverable(root, ada_name, ada)

    def _add_session_page(
        self,
        root: etree._Element,
        ada_name: str,
        sesion: dict[str, Any],
    ) -> None:
        """Pagina de contenido no evaluable para una sesion de la ADA."""
        question = etree.SubElement(root, "question", type="description")

        numero = sesion.get("sesion")
        tema = sesion.get("tema") or "Sesion"
        name = etree.SubElement(question, "name")
        name_text = etree.SubElement(name, "text")
        sesion_label = f"Sesion {numero}" if numero is not None else "Sesion"
        name_text.text = f"{ada_name} - {sesion_label} - {tema}"

        question_text = etree.SubElement(question, "questiontext", format="html")
        text = etree.SubElement(question_text, "text")

        duracion = sesion.get("duracion_min")
        html_parts: list[str] = [
            f"<h4>SESION {self._escape(str(numero or ''))}"
            f" ({self._escape(str(duracion or ''))} minutos) - {self._escape(tema)}</h4>"
        ]
        objetivo = sesion.get("objetivo_especifico") or sesion.get("objetivo")
        if objetivo:
            html_parts.append(f"<p><strong>Objetivo especifico:</strong> {self._escape(str(objetivo))}</p>")

        resumen = sesion.get("resumen_datos_esenciales") or []
        if resumen:
            html_parts.append("<p><strong>Resumen de los datos esenciales de los temas a tratar</strong></p><ul>")
            for item in resumen:
                html_parts.append(f"<li>{self._escape(str(item))}</li>")
            html_parts.append("</ul>")

        for etiqueta, clave, detalle_clave in (
            ("INICIO", "inicio", "inicio_actividades"),
            ("DESARROLLO", "desarrollo", "desarrollo_actividades"),
            ("CIERRE", "cierre", "cierre_actividades"),
        ):
            fase = sesion.get(clave)
            fase_min = ""
            if isinstance(fase, dict):
                fase_min = str(fase.get("duracion_min") or "")
            html_parts.append(
                f"<p><strong>{etiqueta} ({self._escape(fase_min)} minutos)</strong></p>"
            )

            detalle = sesion.get(detalle_clave) or []
            if detalle:
                html_parts.append("<ol>")
                for item in detalle:
                    html_parts.append(f"<li>{self._escape(str(item))}</li>")
                html_parts.append("</ol>")
            elif fase:
                html_parts.append(f"<p>{self._escape(self._phase_text(fase))}</p>")

        text.text = etree.CDATA("".join(html_parts))

        default_grade = etree.SubElement(question, "defaultgrade")
        default_grade.text = "0"

    def _add_presentation_page(
        self,
        root: etree._Element,
        ada_name: str,
        ada: dict[str, Any],
    ) -> None:
        """Pagina de contenido con la presentacion HTML5 incrustada (iframe srcdoc)."""
        presentacion = ada.get("presentacion") or {}
        html = presentacion.get("html")
        public_url = str(ada.get("presentacion_public_url") or "").strip()
        if not html:
            return

        titulo = presentacion.get("titulo") or "Presentacion interactiva"
        subtitulo = presentacion.get("subtitulo")
        num = presentacion.get("num_diapositivas")

        question = etree.SubElement(root, "question", type="description")

        name = etree.SubElement(question, "name")
        name_text = etree.SubElement(name, "text")
        name_text.text = f"Presentacion - {ada_name}"

        question_text = etree.SubElement(question, "questiontext", format="html")
        text = etree.SubElement(question_text, "text")

        if public_url:
            safe_url = self._escape(public_url)
            iframe = (
                f'<iframe src="{safe_url}" '
                'style="width:100%;height:520px;border:1px solid #c9a24a;'
                'border-radius:8px;background:#0b1e3f;" '
                'loading="lazy" referrerpolicy="no-referrer" '
                'title="Presentacion interactiva"></iframe>'
            )
        else:
            # Fallback a srcdoc solo cuando no existe URL publica.
            srcdoc = html.replace("&", "&amp;").replace('"', "&quot;")
            iframe = (
                f'<iframe srcdoc="{srcdoc}" '
                'style="width:100%;height:480px;border:1px solid #c9a24a;'
                'border-radius:8px;background:#0b1e3f;" '
                'sandbox="allow-scripts allow-same-origin" '
                'loading="lazy" title="Presentacion interactiva"></iframe>'
            )

        html_parts: list[str] = [f"<h4>{self._escape(titulo)}</h4>"]
        if subtitulo:
            html_parts.append(f"<p><em>{self._escape(subtitulo)}</em></p>")
        if num:
            html_parts.append(
                f"<p><strong>{self._escape(str(num))} diapositivas</strong> "
                "&middot; usa las flechas \u2190 \u2192 o los botones para navegar.</p>"
            )
        if public_url:
            html_parts.append(
                f"<p><a href=\"{self._escape(public_url)}\" target=\"_blank\" rel=\"noopener\">"
                "Abrir presentacion en nueva pestana</a></p>"
            )
        html_parts.append(f"<p>{iframe}</p>")

        text.text = etree.CDATA("".join(html_parts))

        default_grade = etree.SubElement(question, "defaultgrade")
        default_grade.text = "0"

    def _add_ada_deliverable(
        self,
        root: etree._Element,
        ada_name: str,
        ada: dict[str, Any],
    ) -> None:
        """Unico entregable evaluable de la ADA (una sola tarea por ADA)."""
        question = etree.SubElement(root, "question", type="essay")

        name = etree.SubElement(question, "name")
        name_text = etree.SubElement(name, "text")
        name_text.text = f"Entregable - {ada_name}"

        question_text = etree.SubElement(question, "questiontext", format="html")
        text = etree.SubElement(question_text, "text")

        html_parts: list[str] = []
        wrap_style = (
            "font-family:'Segoe UI',system-ui,sans-serif;max-width:900px;margin:0 auto;"
            "color:#333;line-height:1.55;background:#f8f9fa;padding:16px;border-radius:10px;"
            "border:1px solid #d8dde6;"
        )
        head_style = (
            "background:#002f6c;color:#fff;padding:14px 16px;border-radius:8px;"
            "border-bottom:4px solid #D4AF37;margin-bottom:12px;"
        )
        body_style = "background:#fff;border:1px solid #e1e6ef;border-radius:8px;padding:12px 14px;"

        html_parts.append(f'<div style="{wrap_style}">')
        html_parts.append(f'<div style="{head_style}"><h3 style="margin:0;">Entregable por ADA</h3>')
        html_parts.append(f'<p style="margin:6px 0 0 0;opacity:.95;">{self._escape(ada_name)}</p></div>')
        html_parts.append(f'<div style="{body_style}">')
        objetivo = ada.get("objetivo")
        if objetivo:
            html_parts.append(f"<p><strong>Objetivo:</strong> {self._escape(objetivo)}</p>")

        evidencias = ada.get("evidencias_aprendizaje")
        if isinstance(evidencias, str):
            evidencias_list = [evidencias]
        else:
            evidencias_list = [str(e) for e in (evidencias or []) if str(e).strip()]
        if evidencias_list:
            html_parts.append("<p><strong>Evidencias de aprendizaje:</strong></p>")
            items = "".join(f"<li>{self._escape(e)}</li>" for e in evidencias_list)
            html_parts.append(f"<ul>{items}</ul>")

        instrumento = ada.get("instrumento_evaluacion")
        if instrumento:
            html_parts.append(
                f"<p><strong>Instrumento de evaluacion:</strong> {self._escape(instrumento)}</p>"
            )

        lista = ada.get("lista_cotejo_entregable") or {}
        criterios = lista.get("criterios") or []
        if criterios:
            html_parts.append(
                "<h4 style=\"margin:14px 0 8px;color:#002f6c;border-bottom:2px solid #D4AF37;padding-bottom:4px;\">"
                "Lista de cotejo</h4>"
            )
            html_parts.append(
                "<table style=\"width:100%;border-collapse:collapse;font-size:.94rem;\">"
                "<thead><tr style=\"background:#343a40;color:#fff;\">"
                "<th style=\"padding:8px;border:1px solid #d9dee8;text-align:left;\">Criterio</th>"
                "<th style=\"padding:8px;border:1px solid #d9dee8;width:70px;text-align:center;\">Valor</th>"
                "</tr></thead><tbody>"
            )
            for c in criterios:
                crit = self._escape(str(c.get("criterio") or "").strip())
                if not crit:
                    continue
                val = self._escape(str(c.get("valor") or "1"))
                html_parts.append(
                    "<tr>"
                    f"<td style=\"padding:8px;border:1px solid #e4e8ef;\">{crit}</td>"
                    f"<td style=\"padding:8px;border:1px solid #e4e8ef;text-align:center;\">{val}</td>"
                    "</tr>"
                )
            html_parts.append("</tbody></table>")

        html_parts.append("</div></div>")

        text.text = etree.CDATA("".join(html_parts) or "<p>Entrega tu producto de la ADA.</p>")

        default_grade = etree.SubElement(question, "defaultgrade")
        default_grade.text = "1.0000000"

        response_format = etree.SubElement(question, "responseformat")
        response_format.text = "editor"

    def _add_category(self, root: etree._Element, module_title: str) -> None:
        question = etree.SubElement(root, "question", type="category")
        category = etree.SubElement(question, "category")
        text = etree.SubElement(category, "text")
        text.text = f"$course$/top/{module_title}"

    def _add_multichoice_question(self, root: etree._Element, item: dict[str, Any]) -> None:
        """Reactivo de opcion multiple (single answer) para el banco/quiz de Moodle."""
        opciones = list(item.get("opciones") or [])
        indice_correcta = int(item.get("indice_correcta", 0) or 0)
        if not opciones or indice_correcta >= len(opciones):
            return

        question = etree.SubElement(root, "question", type="multichoice")

        pregunta = str(item.get("pregunta") or "").strip()
        item_id = str(item.get("id") or "").strip()
        ada = str(item.get("ada") or "").strip()
        stem_corto = (pregunta[:60] + "...") if len(pregunta) > 60 else pregunta
        name = etree.SubElement(question, "name")
        name_text = etree.SubElement(name, "text")
        name_text.text = " - ".join(part for part in (item_id, ada, stem_corto) if part)

        question_text = etree.SubElement(question, "questiontext", format="html")
        qt = etree.SubElement(question_text, "text")
        qt.text = etree.CDATA(f"<p>{self._escape(pregunta)}</p>")

        general = str(item.get("retroalimentacion_general") or "").strip()
        general_feedback = etree.SubElement(question, "generalfeedback", format="html")
        gf = etree.SubElement(general_feedback, "text")
        gf.text = etree.CDATA(f"<p>{self._escape(general)}</p>" if general else "")

        etree.SubElement(question, "defaultgrade").text = "1.0000000"
        etree.SubElement(question, "penalty").text = "0.3333333"
        etree.SubElement(question, "hidden").text = "0"
        etree.SubElement(question, "single").text = "true"
        etree.SubElement(question, "shuffleanswers").text = "true"
        etree.SubElement(question, "answernumbering").text = "abc"

        for tag, mensaje in (
            ("correctfeedback", "Respuesta correcta."),
            ("partiallycorrectfeedback", "Respuesta parcialmente correcta."),
            ("incorrectfeedback", "Respuesta incorrecta."),
        ):
            fb = etree.SubElement(question, tag, format="html")
            fb_text = etree.SubElement(fb, "text")
            fb_text.text = mensaje

        justificacion = str(item.get("justificacion_correcta") or "").strip()
        for idx, opcion in enumerate(opciones):
            es_correcta = idx == indice_correcta
            answer = etree.SubElement(
                question,
                "answer",
                fraction="100" if es_correcta else "0",
                format="html",
            )
            ans_text = etree.SubElement(answer, "text")
            ans_text.text = etree.CDATA(f"<p>{self._escape(opcion)}</p>")

            feedback = etree.SubElement(answer, "feedback", format="html")
            fb_text = etree.SubElement(feedback, "text")
            if es_correcta and justificacion:
                fb_text.text = etree.CDATA(f"<p>{self._escape(justificacion)}</p>")
            else:
                fb_text.text = etree.CDATA("")

    def _add_description_question(
        self,
        root: etree._Element,
        module_title: str,
        lesson_title: str,
        lesson_text: str,
        image_path: str | None,
    ) -> None:
        question = etree.SubElement(root, "question", type="description")

        name = etree.SubElement(question, "name")
        name_text = etree.SubElement(name, "text")
        name_text.text = f"{module_title} - {lesson_title}"

        question_text = etree.SubElement(question, "questiontext", format="html")
        text = etree.SubElement(question_text, "text")

        html_parts = [f"<p>{lesson_text}</p>"]
        if image_path:
            html_parts.append(f'<p><img src="{image_path}" alt="{lesson_title}" /></p>')

        text.text = etree.CDATA("".join(html_parts))

        default_grade = etree.SubElement(question, "defaultgrade")
        default_grade.text = "0"

    def _add_activity_question(
        self,
        root: etree._Element,
        module_title: str,
        lesson_title: str,
        activity_text: str,
    ) -> None:
        question = etree.SubElement(root, "question", type="essay")

        name = etree.SubElement(question, "name")
        name_text = etree.SubElement(name, "text")
        name_text.text = f"Actividad - {module_title} - {lesson_title}"

        question_text = etree.SubElement(question, "questiontext", format="html")
        text = etree.SubElement(question_text, "text")
        text.text = etree.CDATA(f"<p>{activity_text}</p>")

        default_grade = etree.SubElement(question, "defaultgrade")
        default_grade.text = "1.0000000"

        response_format = etree.SubElement(question, "responseformat")
        response_format.text = "editor"

    @staticmethod
    def _phase_text(value: Any) -> str:
        """Normaliza el texto de una fase de sesion (inicio/desarrollo/cierre).

        Soporta dict directo y cadenas con dict serializado (legacy), devolviendo
        una salida limpia para Moodle."""
        if value is None:
            return ""

        if isinstance(value, dict):
            mins = value.get("duracion_min")
            instr = str(value.get("instrucciones") or "").strip()
            if mins and instr:
                return f"({mins} min) {instr}"
            if instr:
                return instr
            return str(value)

        if isinstance(value, str):
            txt = value.strip()
            if txt.startswith("{") and "instrucciones" in txt:
                try:
                    parsed = ast.literal_eval(txt)
                    if isinstance(parsed, dict):
                        return MoodleXmlExporter._phase_text(parsed)
                except Exception:
                    pass
            return txt

        return str(value)

    def _add_reading_question(
        self,
        root: etree._Element,
        ada_name: str,
        reading: dict[str, Any],
    ) -> None:
        fundamento = reading.get("fundamento", "Lectura de fundamentacion")
        lectura = reading.get("lectura", "")
        referencias = reading.get("referencias_apa") or []

        question = etree.SubElement(root, "question", type="description")

        name = etree.SubElement(question, "name")
        name_text = etree.SubElement(name, "text")
        name_text.text = f"Lectura - {ada_name} - {fundamento}"

        question_text = etree.SubElement(question, "questiontext", format="html")
        text = etree.SubElement(question_text, "text")

        paragraphs = [
            f"<p>{self._escape(line)}</p>"
            for line in lectura.split("\n")
            if line.strip()
        ]
        html_parts = [f"<h4>{self._escape(fundamento)}</h4>"] + paragraphs

        if referencias:
            html_parts.append("<h5>Referencias (APA 7.ª edición)</h5>")
            refs_html = "".join(f"<li>{self._escape(ref)}</li>" for ref in referencias)
            html_parts.append(f"<ul>{refs_html}</ul>")

        text.text = etree.CDATA("".join(html_parts))

        default_grade = etree.SubElement(question, "defaultgrade")
        default_grade.text = "0"

    @staticmethod
    def _escape(value: str) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )