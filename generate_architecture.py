"""
AWS Architecture Diagram — Court Judgments to Verified Action Plans
Theme 11 | AI for Bharat Hackathon | Centre for e-Governance

Components from design.md:
  - Preprocessing Engine (OpenCV)
  - OCR Engine (AWS Textract)
  - Action Plan Generator (Amazon Bedrock / Claude 3)

Run:    python generate_architecture.py
Output: court_judgment_architecture.png
"""

import os

# ── Fix: ensure Graphviz dot engine is on PATH (Windows) ──────────────────────
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.storage import S3
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.ml import Textract, Sagemaker
from diagrams.aws.engagement import SES
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import IAMRole
from diagrams.aws.general import User

# ── Graph-level styling ────────────────────────────────────────────────────────
graph_attr = {
    "fontsize":  "15",
    "bgcolor":   "#1a1a2e",
    "fontcolor": "#FF9900",
    "fontname":  "Helvetica Neue",
    "pad":       "1.0",
    "splines":   "ortho",
    "nodesep":   "0.8",
    "ranksep":   "1.2",
    "labelloc":  "t",
}

node_attr = {
    "fontsize":  "10",
    "fontcolor": "#ffffff",
    "fontname":  "Helvetica Neue",
}

edge_attr = {
    "color":     "#FF9900",
    "fontsize":  "9",
    "fontcolor": "#FF9900",
    "fontname":  "Helvetica Neue",
}

with Diagram(
    "Court Judgments → Verified Action Plans\n"
    "Theme 11  |  AI for Bharat Hackathon  |  Centre for e-Governance",
    filename="court_judgment_architecture",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):

    # ── Users ──────────────────────────────────────────────────────────────────
    with Cluster(
        "Government Users",
        graph_attr={"bgcolor": "#16213e", "fontcolor": "#ffffff", "style": "rounded"},
    ):
        nodal_officer = User("Nodal Officer\nUpload · Review · Verify")
        dept_head     = User("Department Head\nApprove · Reject")

    # ── LOCAL cluster — Preprocessing Engine ──────────────────────────────────
    with Cluster(
        "Local  —  Preprocessing Engine (OpenCV)",
        graph_attr={"bgcolor": "#2d1b4e", "fontcolor": "#ffffff", "style": "rounded"},
    ):
        l_pre = Lambda("Preprocessing Lambda\nOpenCV Pipeline")
        # OpenCV steps represented as a note node via a plain custom label
        # (diagrams doesn't have an OpenCV icon; Lambda is the compute host)
        opencv_steps = Lambda(
            "OpenCV Steps\n"
            "① Grayscale\n"
            "② Gaussian Blur\n"
            "③ Otsu Threshold\n"
            "④ Hough Lines\n"
            "⑤ Affine Rotation\n"
            "⑥ CLAHE Contrast"
        )
        s3_proc = S3("S3\nprocessed-text/\n(300 DPI PNGs)")

    # ── CLOUD cluster — AWS Services ───────────────────────────────────────────
    with Cluster(
        "Cloud  —  AWS  (ap-south-1)",
        graph_attr={"bgcolor": "#0f3460", "fontcolor": "#ffffff", "style": "rounded"},
    ):

        with Cluster(
            "Ingestion & Storage",
            graph_attr={"bgcolor": "#1a3a1a", "fontcolor": "#ffffff"},
        ):
            s3_raw   = S3("S3\nraw-documents/")
            s3_plans = S3("S3\naction-plans/")
            s3_exp   = S3("S3\nexports/")
            ddb      = Dynamodb("DynamoDB\nDoc State + Audit Log")

        with Cluster(
            "OCR Engine  —  AWS Textract",
            graph_attr={"bgcolor": "#3b1f5e", "fontcolor": "#ffffff"},
        ):
            l_ocr    = Lambda("OCR Lambda")
            textract = Textract(
                "AWS Textract\n"
                "LAYOUT · TABLES · FORMS\n"
                "Async Document Analysis\n"
                "Confidence Scoring"
            )

        with Cluster(
            "Action Plan Generator  —  Amazon Bedrock",
            graph_attr={"bgcolor": "#5e1f1f", "fontcolor": "#ffffff"},
        ):
            l_ext   = Lambda("Extraction Lambda")
            bedrock = Sagemaker(
                "Amazon Bedrock\n"
                "Claude 3 Sonnet\n"
                "Converse API\n"
                "temperature=0.0"
            )

        with Cluster(
            "Orchestration & Observability",
            graph_attr={"bgcolor": "#1f3a5e", "fontcolor": "#ffffff"},
        ):
            l_orc = Lambda("Orchestrator Lambda\nPipeline Trigger")
            ses   = SES("Amazon SES\nFailure Alerts")
            cw    = Cloudwatch("CloudWatch\nLogs · Metrics")
            iam   = IAMRole("IAM + KMS\nRBAC · Encryption")

        with Cluster(
            "Presentation Layer",
            graph_attr={"bgcolor": "#1f1f3a", "fontcolor": "#ffffff"},
        ):
            dashboard  = Lambda("Streamlit Dashboard\nHiTL Verification UI")
            export_svc = Lambda("Export Service\nPDF · JSON Reports")

    # ── Connections ────────────────────────────────────────────────────────────

    # Users → Dashboard
    nodal_officer >> Edge(label="HTTPS/TLS 1.3", color="#1A73E8") >> dashboard
    dept_head     >> Edge(label="HTTPS/TLS 1.3", color="#1A73E8") >> dashboard

    # Dashboard → S3 upload
    dashboard >> Edge(label="PutObject") >> s3_raw

    # Dashboard ↔ DynamoDB
    dashboard >> Edge(label="Read State", style="dashed", color="#3B48CC") >> ddb
    ddb       >> Edge(label="Status Updates", style="dashed", color="#3B48CC") >> dashboard

    # S3 event → Orchestrator
    s3_raw >> Edge(label="s3:ObjectCreated\nevent trigger", color="#FF9900") >> l_orc

    # Orchestrator → Preprocessing
    l_orc >> Edge(label="Invoke + doc_id") >> l_pre
    l_orc >> Edge(label="State transitions", style="dashed", color="#3B48CC") >> ddb

    # Preprocessing internal flow
    l_pre >> Edge(label="Apply pipeline") >> opencv_steps
    opencv_steps >> Edge(label="Corrected image\n300 DPI PNG") >> s3_proc
    l_pre >> Edge(label="Audit events", style="dashed", color="#3B48CC") >> ddb

    # Preprocessing → OCR
    s3_proc >> Edge(label="Page images") >> l_ocr

    # OCR Engine
    l_ocr >> Edge(label="StartDocumentAnalysis") >> textract
    textract >> Edge(label="Blocks + Confidence\nScores") >> l_ocr
    l_ocr >> Edge(label="ocr_result.json\n+ low-confidence flags") >> s3_proc
    l_ocr >> Edge(label="Invoke + ocr_key") >> l_ext
    l_ocr >> Edge(label="Audit events", style="dashed", color="#3B48CC") >> ddb

    # Action Plan Generator
    l_ext >> Edge(label="Converse API\nStructured Prompt") >> bedrock
    bedrock >> Edge(label="Directives JSON\n+ Source Offsets") >> l_ext
    l_ext >> Edge(label="action_plan.json") >> s3_plans
    l_ext >> Edge(label="Status → pending_review", style="dashed", color="#3B48CC") >> ddb

    # S3 plans → Dashboard
    s3_plans >> Edge(label="Load for Review", style="dashed") >> dashboard

    # Export flow
    dashboard  >> Edge(label="Generate Export") >> export_svc
    export_svc >> Edge(label="Store Copy") >> s3_exp

    # Failure path
    l_orc >> Edge(label="On Failure\n(3 retries)", color="#E7157B") >> ses
    ses   >> Edge(label="Email Alert", color="#E7157B") >> nodal_officer

    # All Lambdas → CloudWatch
    for node in [l_orc, l_pre, l_ocr, l_ext]:
        node >> Edge(label="Logs", style="dashed", color="#888888") >> cw

    # IAM → DynamoDB (immutability enforcement)
    iam >> Edge(
        label="Deny DeleteItem\nUpdateItem on audit",
        style="dashed",
        color="#DD344C",
    ) >> ddb


print("✅  Diagram saved → court_judgment_architecture.png")
