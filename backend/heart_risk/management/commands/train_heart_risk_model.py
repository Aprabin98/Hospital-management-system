from django.core.management.base import BaseCommand, CommandError

from heart_risk.ml_engine import train_and_save_model


class Command(BaseCommand):
    help = 'Train and persist ML heart-risk model using online real dataset (OpenML).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Fetching online dataset and training model...'))
        try:
            metadata = train_and_save_model()
        except Exception as exc:
            raise CommandError(f'Model training failed: {exc}') from exc

        metrics = metadata.get('metrics', {})
        source = metadata.get('source', {})
        selected_model = metadata.get('model_type', 'Unknown')
        candidate_results = metadata.get('candidate_results', {})

        self.stdout.write(self.style.SUCCESS('Heart-risk model trained and saved successfully.'))
        self.stdout.write(f"Source: {source.get('dataset_name')} | Samples: {source.get('samples_used')}")
        self.stdout.write(f"Selected model: {selected_model}")
        self.stdout.write(
            (
                'Metrics '
                f"AUC={metrics.get('roc_auc', 0):.3f}, "
                f"Accuracy={metrics.get('accuracy', 0):.3f}, "
                f"Precision={metrics.get('precision', 0):.3f}, "
                f"Recall={metrics.get('recall', 0):.3f}, "
                f"F1={metrics.get('f1', 0):.3f}"
            )
        )

        if candidate_results:
            self.stdout.write('Candidate comparison (AUC):')
            for name, result in candidate_results.items():
                self.stdout.write(f" - {name}: {result.get('roc_auc', 0):.3f}")
