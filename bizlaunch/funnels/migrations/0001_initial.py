# Generated by Django 5.1.6 on 2025-02-28 14:01

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FunnelTemplate',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PageTemplate',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('layout', models.CharField(help_text="e.g., 'optin', 'sales', 'thankyou'", max_length=50)),
                ('order_in_funnel', models.PositiveIntegerField(default=1, help_text='Order in which this page appears within the funnel.')),
                ('funnel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='funnels.funneltemplate')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PageImage',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('image_content', models.BinaryField(blank=True, null=True)),
                ('components', models.JSONField(default=dict, help_text='JSON structure defining components like headlines, subheadings, CTAs, forms, etc.')),
                ('order', models.PositiveIntegerField(default=1, help_text='Order in which this image appears in the page.')),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='funnels.pagetemplate')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SystemFunnelAssociation',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('order_in_system', models.PositiveIntegerField(default=1, help_text='Order in which this funnel appears under the system.')),
                ('funnel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='funnels.funneltemplate')),
            ],
            options={
                'ordering': ['order_in_system'],
            },
        ),
        migrations.CreateModel(
            name='SystemTemplate',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('funnels', models.ManyToManyField(related_name='systems', through='funnels.SystemFunnelAssociation', to='funnels.funneltemplate')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='systemfunnelassociation',
            name='system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='funnels.systemtemplate'),
        ),
        migrations.AlterUniqueTogether(
            name='systemfunnelassociation',
            unique_together={('system', 'funnel')},
        ),
    ]
