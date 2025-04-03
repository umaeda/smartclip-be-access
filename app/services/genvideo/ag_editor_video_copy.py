import random
from typing import List

from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip, TextClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import  CrossFadeIn
from moviepy import *

# --- Agente de Edição de Vídeo ---
class EditorVideo:


    # def zoom_in(self, clip, factor=1.2, x_center=None, y_center=None):
    #     """
    #     Aplica um efeito de zoom-in dinâmico no clipe.
    #
    #     Parâmetros:
    #         clip: O clipe de vídeo ou imagem.
    #         factor: Fator final de zoom (padrão 1.2).
    #         x_center: Coordenada x do ponto central para o zoom.
    #         y_center: Coordenada y do ponto central para o zoom.
    #                   Se não informados, será escolhido aleatoriamente entre:
    #                     - Centro
    #                     - Quadrante superior esquerdo
    #                     - Quadrante superior direito
    #                     - Quadrante inferior esquerdo
    #                     - Quadrante inferior direito
    #
    #     Retorna:
    #         Um novo clipe com efeito de zoom-in aplicado.
    #     """
    #     w, h = clip.size
    #     # Se algum dos pontos não for informado, escolhe aleatoriamente entre as opções
    #     if x_center is None or y_center is None:
    #         opcoes = [
    #             (w / 2, h / 2),  # Centro
    #             (w / 4, h / 4),  # Superior esquerdo
    #             (3 * w / 4, h / 4),  # Superior direito
    #             (w / 4, 3 * h / 4),  # Inferior esquerdo
    #             (3 * w / 4, 3 * h / 4)  # Inferior direito
    #         ]
    #         x_center, y_center = random.choice(opcoes)
    #
    #     duration = clip.duration
    #
    #     def dynamic_crop(get_frame, t):
    #         # Calcula o fator de zoom atual com base no tempo
    #         current_factor = 1 + (factor - 1) * (t / duration)
    #         new_w = w / current_factor
    #         new_h = h / current_factor
    #         # Calcula os limites com base no ponto central
    #         x1 = x_center - new_w / 2
    #         y1 = y_center - new_h / 2
    #         x2 = x_center + new_w / 2
    #         y2 = y_center + new_h / 2
    #
    #         # Garante que os limites não extrapolem os da imagem
    #         x1 = max(0, x1)
    #         y1 = max(0, y1)
    #         x2 = min(w, x2)
    #         y2 = min(h, y2)
    #
    #         frame = get_frame(t)
    #         return frame[int(y1):int(y2), int(x1):int(x2)]
    #
    #     # Aplica o recorte dinâmico e, em seguida, redimensiona para o tamanho original.
    #     cropped_clip = clip.fl(dynamic_crop, apply_to=["mask"])
    #     return cropped_clip.resize(clip.size)

    def zoom_in(self, clip, fact=1.2, x_center=None, y_center=None):
        """
        Aplica um efeito de zoom-in dinâmico ao clipe, criando um novo VideoClip
        com frames modificados.

        Parâmetros:
            clip: Um ImageClip (ou outro clipe estático).
            fact: Fator final de zoom (padrão 1.2).
            x_center: Coordenada x do ponto central para o zoom.
            y_center: Coordenada y do ponto central para o zoom.
                     Se não informados, escolhe aleatoriamente entre centro e cantos.

        Retorna:
            Um novo VideoClip com o efeito de zoom-in aplicado.
        """
        w, h = clip.size
        duration = clip.duration

        # Se não for passado um ponto de zoom, escolhe aleatoriamente
        if x_center is None or y_center is None:
            opcoes = [
                (w / 2, h / 2),  # Centro
                (w / 4, h / 4),  # Superior esquerdo
                (3 * w / 4, h / 4),  # Superior direito
                (w / 4, 3 * h / 4),  # Inferior esquerdo
                (3 * w / 4, 3 * h / 4)  # Inferior direito
            ]
            x_center, y_center = random.choice(opcoes)

        def dynamic_crop_frame(t):
            # Calcula o fator de zoom atual (linearmente de 1 até fact)
            current_factor = 1 + (fact - 1) * (t / duration)
            new_w = w / current_factor
            new_h = h / current_factor

            # Calcula os limites do recorte com base no ponto central
            x1 = x_center - new_w / 2
            y1 = y_center - new_h / 2
            x2 = x_center + new_w / 2
            y2 = y_center + new_h / 2

            # Garante que os limites não ultrapassem os da imagem
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            # Obtém o frame original
            frame = clip.get_frame(t)
            # Converte os limites para inteiros e recorta o frame
            return frame[int(y1):int(y2), int(x1):int(x2)]

        # Cria um novo VideoClip usando a função de frame personalizada
        new_clip = VideoClip(frame_function=dynamic_crop_frame, duration=duration)

        # Redimensiona o novo clipe para ter o mesmo tamanho do clipe original
        new_clip = new_clip.resized(width=1080, height=1080)

        return new_clip
        VideoFileClip

    def crossfade_transition(self, clips: List[VideoClip], transition_duration=3):
        """
        Combina uma lista de clipes aplicando uma transição suave de fade cruzado.

        Parâmetros:
            clips: Lista de clipes.
            transition_duration: Duração da transição entre clipes (padrão: 3 segundos).

        Retorna:
            Um clipe final com as transições aplicadas.
        """

        new_clips = []
        start_time = 0
        for i, clip in enumerate(clips):
            # Para clipes após o primeiro, inicia sobrepondo o fade
            if i > 0:
                start_time = new_clips[-1].end - transition_duration
            clip = clip.with_layer_index(0)
            clip = clip.with_start(start_time)
              # Aplica o fade in para clipes exceto o primeiro
            if i > 0:
                x = CrossFadeIn(3)
                clip = x.apply(clip)
            new_clips.append(clip)
        final_clip = CompositeVideoClip(new_clips)
        final_clip.duration = new_clips[-1].end
        return final_clip

    def adicionar_legenda(self, video, texto, ftname='Impact', fontsize=30, color='white', position=None):
        """
        Adiciona legendas ao vídeo, sincronizadas com o áudio.

        Parâmetros:
            video: O clipe de vídeo original.
            texto: Texto completo da narração.
            fontname: Fonte usada nas legendas (padrão: 'Impact').
            fontsize: Tamanho da fonte (padrão: 36).
            color: Cor do texto.
            position: Posição das legendas no vídeo. Se None, posiciona 20% acima da base.

        Retorna:
            Um clipe (CompositeVideoClip) com as legendas sobrepostas.
        """
        if position is None:
            position = ("center", video.h * 0.8)

        if "\n" in texto:
            segments = [seg.strip() for seg in texto.split("\n") if seg.strip()]
        else:
            segments = [seg.strip() for seg in texto.split(".") if seg.strip()]

        num_segments = len(segments)
        dur_seg = video.duration / num_segments

        subs = []
        for i, seg in enumerate(segments):
            start = i * dur_seg
            end = start + dur_seg
            subs.append(((start, end), seg))

        # Função para criar o TextClip; recebe argumentos extras e remove "font" se já estiver presente.
        def make_txtclip(txt, **kwargs):
            text_clip = TextClip(
                text=txt,
                font="C:/Windows/Fonts/impact.ttf",
                font_size=24,
                color="white",
                bg_color=None,
                stroke_color=None,
                stroke_width=0
            ).with_position("center").with_duration(10)
            return text_clip

        subtitles = SubtitlesClip(subs, make_textclip=make_txtclip)
        subtitles = subtitles.with_position(position)
        return CompositeVideoClip([video, subtitles])


    # def adicionar_legenda(self, video, texto, fontname='Impact', fontsize=36, color='white', position=None):
    #     """
    #     Adiciona legendas ao vídeo, sincronizadas com o áudio.
    #
    #     O método divide o texto em partes (utilizando quebras de linha ou pontos)
    #     e distribui de forma igual ao longo da duração do vídeo.
    #
    #     Parâmetros:
    #         video: O clipe de vídeo original.
    #         texto: Texto completo da narração.
    #         font: Fonte usada nas legendas (padrão: 'Impact').
    #         fontsize: Tamanho da fonte (padrão: 36).
    #         color: Cor do texto.
    #         position: Posição das legendas no vídeo. Se None, posiciona 20% acima da base.
    #
    #     Retorna:
    #         Um clipe (CompositeVideoClip) com as legendas sobrepostas.
    #     """
    #     # Define a posição padrão: centralizado horizontalmente e 20% acima da base
    #     if position is None:
    #         position = ("center", video.h * 0.8)
    #
    #     # Divide o texto em segmentos (utilizando quebras de linha ou pontos)
    #     if "\n" in texto:
    #         segments = [seg.strip() for seg in texto.split("\n") if seg.strip()]
    #     else:
    #         segments = [seg.strip() for seg in texto.split(".") if seg.strip()]
    #
    #     num_segments = len(segments)
    #     dur_seg = video.duration / num_segments
    #
    #     # Cria uma lista de tuplas ((start, end), texto) para cada segmento
    #     subs = []
    #     for i, seg in enumerate(segments):
    #         start = i * dur_seg
    #         end = start + dur_seg
    #         subs.append(((start, end), seg))
    #
    #     # Função para criar o TextClip para cada legenda
    #     def make_txtclip(txt):
    #         return TextClip(txt, font=fontname, fontsize=fontsize, color=color, method='caption',
    #                         size=(video.w * 0.8, None))
    #
    #     subtitles = SubtitlesClip(subs, make_textclip=make_txtclip)
    #     subtitles = subtitles.with_position(position)
    #     # Combina o vídeo original com as legendas
    #     return CompositeVideoClip([video, subtitles])

    def criar_animacao(self, imagens, audio_path="narracao.mp3", transition_duration=3, legenda_texto=None, identificador='123'):
        audio = AudioFileClip(audio_path)
        duracao = audio.duration

        clips = []
        num_imgs = len(imagens)
        clip_duration = (duracao + (num_imgs - 1) * transition_duration) / num_imgs

        for img in imagens:
            clip = ImageClip(img).with_duration(clip_duration)
            # Aplica redimensionamento via efeito
            clip = clip.resized(width=1080, height=1080)

            # Se tiver um zoom_in customizado, aplique aqui
            clip = self.zoom_in(clip, fact=2)
            clips.append(clip)

        if len(clips) > 1:
            video = self.crossfade_transition(clips, transition_duration=transition_duration)
        else:
            video = clips[0]

        video = video.with_duration(duracao)
        video = video.with_audio(audio)

        if legenda_texto:
            video = self.adicionar_legenda(video, legenda_texto)

        output = f"{identificador}.mp4"

        video.write_videofile(output, fps=26, codec='libx264')

        return output

